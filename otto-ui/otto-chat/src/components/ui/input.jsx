import React from "react"

export function Input({ value, onChange, placeholder = "", disabled = false, className = "" }) {
  return (
    <input
      type="text"
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled}
      className={`w-full p-2 border border-gray-300 rounded-xl focus:outline-none focus:ring focus:border-[#004d40] ${className}`}
    />
  )
}