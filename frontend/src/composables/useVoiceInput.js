/**
 * Voice Input Composable
 *
 * Manages voice recording and transcription.
 */

import { ref, computed } from 'vue'
import { API_URLS } from '@/config/endpoints'
import { VOICE_CONFIG } from '@/config/constants'
import { ErrorHandler, NetworkError } from '@/utils/errorHandler'

export function useVoiceInput() {
  const isRecordingVoice = ref(false)
  const mediaRecorder = ref(null)
  const audioChunks = ref([])

  /**
   * Voice input icon
   */
  const voiceInputIcon = computed(() => {
    return isRecordingVoice.value ? 'fa-stop-circle' : 'fa-microphone'
  })

  /**
   * Check if browser supports voice input
   */
  const isVoiceSupported = computed(() => {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
  })

  /**
   * Start voice recording
   */
  async function startRecording() {
    if (!isVoiceSupported.value) {
      throw new Error('Voice input is not supported in this browser')
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      mediaRecorder.value = new MediaRecorder(stream)
      audioChunks.value = []

      mediaRecorder.value.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.value.push(event.data)
        }
      }

      mediaRecorder.value.start()
      isRecordingVoice.value = true
    } catch (error) {
      ErrorHandler.logError(error, 'useVoiceInput.startRecording')
      throw new Error('Failed to access microphone. Please check permissions.')
    }
  }

  /**
   * Stop voice recording and transcribe
   * @returns {Promise<string>} Transcribed text
   */
  async function stopRecording() {
    return new Promise((resolve, reject) => {
      if (!mediaRecorder.value || mediaRecorder.value.state === 'inactive') {
        reject(new Error('No active recording'))
        return
      }

      mediaRecorder.value.onstop = async () => {
        try {
          const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' })

          // Stop all tracks
          const tracks = mediaRecorder.value.stream.getTracks()
          tracks.forEach(track => track.stop())

          // Transcribe audio
          const text = await transcribeAudio(audioBlob)

          isRecordingVoice.value = false
          resolve(text)
        } catch (error) {
          isRecordingVoice.value = false
          reject(error)
        }
      }

      mediaRecorder.value.stop()
    })
  }

  /**
   * Toggle voice recording
   * @returns {Promise<string | null>} Transcribed text if stopped, null if started
   */
  async function toggleVoiceInput() {
    if (isRecordingVoice.value) {
      return await stopRecording()
    } else {
      await startRecording()
      return null
    }
  }

  /**
   * Transcribe audio blob to text
   * @param {Blob} audioBlob - Audio data
   * @returns {Promise<string>} Transcribed text
   */
  async function transcribeAudio(audioBlob) {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'recording.webm')

    try {
      const response = await fetch(API_URLS.transcribeAudio(), {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (!response.ok) {
        throw new NetworkError(`Transcription failed: ${response.statusText}`)
      }

      const data = await response.json()

      if (data.text) {
        return data.text
      } else {
        throw new Error('No transcription result')
      }
    } catch (error) {
      const appError = ErrorHandler.handleApiError(error)
      ErrorHandler.logError(appError, 'useVoiceInput.transcribeAudio')
      throw new Error('Failed to transcribe audio. Please try again.')
    }
  }

  /**
   * Cancel recording without transcribing
   */
  function cancelRecording() {
    if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
      const tracks = mediaRecorder.value.stream.getTracks()
      tracks.forEach(track => track.stop())
      mediaRecorder.value.stop()
    }

    isRecordingVoice.value = false
    audioChunks.value = []
  }

  return {
    isRecordingVoice,
    voiceInputIcon,
    isVoiceSupported,
    startRecording,
    stopRecording,
    toggleVoiceInput,
    cancelRecording
  }
}
