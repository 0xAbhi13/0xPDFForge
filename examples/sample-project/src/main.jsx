import React from "react"
import { motion } from "framer-motion"
import axios from "axios"

export default function App(){
  fetch("/api/projects").then(r=>r.json()).then(console.log)
  axios.get("/api/user")
  axios.post("/api/contact", {email: "test@example.com"})
  localStorage.setItem("theme","dark")
  document.querySelector("#hero")
  document.addEventListener("click", ()=>{})
  return <motion.div>hello</motion.div>
}
