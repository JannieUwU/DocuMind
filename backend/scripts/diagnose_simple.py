"""
Simple diagnostic script for conversation isolation
"""
import sqlite3
import sys
from pathlib import Path

def diagnose(username):
    print("\n" + "="*60)
    print(f"Diagnosing user: {username}")
    print("="*60 + "\n")

    # Check databases
    users_db = "users.db"
    rag_db = f"custom_rag_{username}.db"

    if not Path(users_db).exists():
        print(f"[ERROR] Database not found: {users_db}")
        return

    # Get user ID
    conn = sqlite3.connect(users_db)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_row = cursor.fetchone()

    if not user_row:
        print(f"[ERROR] User not found: {username}")
        return

    user_id = user_row[0]
    print(f"[OK] User ID: {user_id}\n")

    # Check conversations
    print("="*60)
    print("CONVERSATIONS")
    print("="*60)

    cursor.execute("""
        SELECT id, title, created_at, updated_at
        FROM conversations
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    conversations = cursor.fetchall()

    if not conversations:
        print("No conversations found\n")
    else:
        for conv_id, title, created, updated in conversations:
            cursor.execute("""
                SELECT COUNT(*) FROM messages WHERE conversation_id = ?
            """, (conv_id,))
            msg_count = cursor.fetchone()[0]

            print(f"Conversation ID: {conv_id}")
            print(f"  Title: {title}")
            print(f"  Messages: {msg_count}")
            print(f"  Created: {created}")
            print(f"  Updated: {updated}")
            print()

    # Check documents
    print("="*60)
    print("DOCUMENTS")
    print("="*60)

    cursor.execute("""
        SELECT id, filename, conversation_id, uploaded_at
        FROM user_documents
        WHERE user_id = ?
        ORDER BY uploaded_at DESC
    """, (user_id,))

    documents = cursor.fetchall()

    if not documents:
        print("No documents found\n")
    else:
        for doc_id, filename, conv_id, uploaded in documents:
            binding = f"Bound to conversation {conv_id}" if conv_id else "[WARNING] NOT BOUND (NULL)"
            print(f"Document: {filename}")
            print(f"  ID: {doc_id}")
            print(f"  {binding}")
            print(f"  Uploaded: {uploaded}")
            print()

    conn.close()

    # Check RAG database
    if not Path(rag_db).exists():
        print(f"[INFO] RAG database not found: {rag_db}")
        print("(This is normal if no files have been uploaded)\n")
        return

    print("="*60)
    print(f"RAG DATABASE: {rag_db}")
    print("="*60)

    conn_rag = sqlite3.connect(rag_db)
    cursor_rag = conn_rag.cursor()

    # Check chunks by conversation_id
    cursor_rag.execute("""
        SELECT conversation_id, COUNT(*) as chunk_count
        FROM chunks
        GROUP BY conversation_id
        ORDER BY conversation_id
    """)

    rag_conversations = cursor_rag.fetchall()

    if not rag_conversations:
        print("No chunks found\n")
    else:
        print("\nChunks grouped by conversation_id:")
        print("-" * 60)

        total_chunks = 0
        null_chunks = 0

        for conv_id, count in rag_conversations:
            total_chunks += count

            if conv_id is None:
                null_chunks = count
                print(f"[WARNING] NULL (unbound): {count} chunks")
            else:
                print(f"Conversation {conv_id}: {count} chunks")

        print("-" * 60)
        print(f"Total chunks: {total_chunks}")

        if null_chunks > 0:
            print(f"\n[CRITICAL] Found {null_chunks} unbound chunks (conversation_id=NULL)")
            print("These chunks may cause cross-conversation data leakage!")
            print("\nTo see which documents:")

            cursor_rag.execute("""
                SELECT DISTINCT document_id, COUNT(*) as count
                FROM chunks
                WHERE conversation_id IS NULL
                GROUP BY document_id
            """)

            null_docs = cursor_rag.fetchall()
            for doc_id, count in null_docs:
                cursor_rag.execute("SELECT filename FROM documents WHERE id = ?", (doc_id,))
                filename_row = cursor_rag.fetchone()
                filename = filename_row[0] if filename_row else "Unknown"
                print(f"  - Document ID {doc_id} ({filename}): {count} chunks")

            print("\nRECOMMENDATION:")
            print("  1. Delete unbound chunks from RAG database")
            print("  2. Ensure conversation_id is passed when uploading files")
            print("  3. Test if new conversations still see old files")

    conn_rag.close()

    print("\n" + "="*60)
    print("DIAGNOSTIC COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "Jade"
    diagnose(username)
