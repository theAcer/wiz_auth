"use client"

import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { supabase } from "../../lib/supabase"

export default function AuthCallback() {
  const [message, setMessage] = useState("Processing authentication...")
  const navigate = useNavigate()

  useEffect(() => {
    const handleAuthCallback = async () => {
      const { error } = await supabase.auth.getSession()

      if (error) {
        setMessage("Error authenticating: " + error.message)
        setTimeout(() => navigate("/login"), 3000)
      } else {
        setMessage("Authentication successful! Redirecting...")
        setTimeout(() => navigate("/profile"), 1000)
      }
    }

    handleAuthCallback()
  }, [navigate])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full mx-auto bg-white p-8 rounded-lg shadow-md text-center">
        <h2 className="text-2xl font-bold mb-4">Authentication</h2>
        <p>{message}</p>
      </div>
    </div>
  )
}

