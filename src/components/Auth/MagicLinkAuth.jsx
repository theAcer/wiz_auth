"use client"

import { useState } from "react"
import { useAuth } from "../../context/AuthContext"

export default function MagicLinkAuth() {
  const { signInWithOtp } = useAuth()
  const [email, setEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)

  const handleMagicLinkLogin = async (e) => {
    e.preventDefault()
    try {
      setLoading(true)
      setMessage(null)

      const { error } = await signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      })

      if (error) throw error

      setMessage("Check your email for the login link!")
    } catch (error) {
      console.error("Error sending magic link:", error.message)
      setMessage("Error sending magic link: " + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleMagicLinkLogin} className="space-y-4">
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          Email
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Your email"
          required
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
      >
        {loading ? "Sending..." : "Send Magic Link"}
      </button>

      {message && <div className="text-sm text-center mt-2 text-indigo-600">{message}</div>}
    </form>
  )
}

