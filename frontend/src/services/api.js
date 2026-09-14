/**
 * TruthLens AI — API service layer
 * Path: frontend/src/services/api.js
 */

import axios from 'axios'

const client = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api`,
})

export async function checkHealth() {
  const { data } = await client.get('/health')
  return data
}

export async function uploadVideo(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)

  const { data } = await client.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        onProgress(Math.round((event.loaded * 100) / event.total))
      }
    },
  })
  return data
}

export async function analyzeCase(caseId) {
  const { data } = await client.post(`/analyze/${caseId}`)
  return data
}