import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [message, setMessage] = useState('Connecting to Flask...')

  useEffect(() => {
    fetch('http://127.0.0.1:5000/api/health')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Request failed')
        }

        return response.json()
      })
      .then((data) => setMessage(data.message))
      .catch(() => setMessage('Could not connect to Flask'))
  }, [])

  return (
    <main>
      <h1>TaskFlow</h1>
      <p>{message}</p>
    </main>
  )
}

export default App