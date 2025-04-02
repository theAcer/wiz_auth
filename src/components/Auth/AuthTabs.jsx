"use client"

import { useState } from "react"
import GoogleAuth from "./GoogleAuth"
import MagicLinkAuth from "./MagicLinkAuth"
import PhoneAuth from "./PhoneAuth"

export default function AuthTabs() {
  const [activeTab, setActiveTab] = useState("magic")

  return (
    <div className="max-w-md w-full mx-auto bg-white p-8 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-center mb-6">Sign In / Sign Up</h2>

      <div className="flex border-b mb-6">
        <button
          className={`flex-1 py-2 text-center ${activeTab === "magic" ? "border-b-2 border-indigo-600 text-indigo-600" : "text-gray-500"}`}
          onClick={() => setActiveTab("magic")}
        >
          Email
        </button>
        <button
          className={`flex-1 py-2 text-center ${activeTab === "phone" ? "border-b-2 border-indigo-600 text-indigo-600" : "text-gray-500"}`}
          onClick={() => setActiveTab("phone")}
        >
          Phone
        </button>
      </div>

      {activeTab === "magic" && <MagicLinkAuth />}
      {activeTab === "phone" && <PhoneAuth />}

      <div className="mt-6">
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white text-gray-500">Or continue with</span>
          </div>
        </div>

        <div className="mt-6">
          <GoogleAuth />
        </div>
      </div>
    </div>
  )
}

