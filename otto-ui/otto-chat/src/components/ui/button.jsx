import React from "react"

export function Button({ children, onClick, type = "button", disabled = false, className = "" }) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`bg-[#004d40] text-white px-4 py-2 rounded-xl hover:opacity-90 disabled:opacity-50 ${className}`}
    >
      {children}
    </button>
  )
}
