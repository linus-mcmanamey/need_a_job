/**
 * WebSocket Client for Real-time Updates
 *
 * Provides WebSocket connection management with auto-reconnect capability
 * and message handler registration.
 */

// Get WebSocket URL from environment variables
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/status'

// Reconnect delay in milliseconds
const RECONNECT_DELAY = 3000

/**
 * WebSocket Client Class
 *
 * Manages WebSocket connection lifecycle, message handling, and auto-reconnect.
 */
class WebSocketClient {
  constructor() {
    this.ws = null
    this.messageHandlers = new Map()
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 10
    this.isIntentionallyClosed = false
    this.reconnectTimer = null
  }

  /**
   * Connect to WebSocket server
   * @returns {Promise<void>}
   */
  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected')
      return Promise.resolve()
    }

    return new Promise((resolve, reject) => {
      try {
        console.log(`[WebSocket] Connecting to ${WS_URL}`)
        this.ws = new WebSocket(WS_URL)
        this.isIntentionallyClosed = false

        this.ws.onopen = () => {
          console.log('[WebSocket] Connected successfully')
          this.reconnectAttempts = 0
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data)
            console.log('[WebSocket] Message received:', message)
            this.handleMessage(message)
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('[WebSocket] Error:', error)
          reject(error)
        }

        this.ws.onclose = (event) => {
          console.log(`[WebSocket] Connection closed (code: ${event.code})`)
          this.ws = null

          // Attempt to reconnect unless intentionally closed
          if (!this.isIntentionallyClosed) {
            this.scheduleReconnect()
          }
        }
      } catch (error) {
        console.error('[WebSocket] Connection error:', error)
        reject(error)
      }
    })
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    console.log('[WebSocket] Disconnecting...')
    this.isIntentionallyClosed = true

    // Clear any pending reconnect timers
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  /**
   * Schedule automatic reconnection
   */
  scheduleReconnect() {
    // Clear any existing reconnect timer before scheduling new one
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnect attempts reached')
      return
    }

    this.reconnectAttempts++
    console.log(
      `[WebSocket] Reconnecting in ${RECONNECT_DELAY}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    )

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null // Clear the timer reference after it executes
      this.connect().catch((error) => {
        console.error('[WebSocket] Reconnection failed:', error)
        // Timer is already cleared above, scheduleReconnect will be called from onclose
      })
    }, RECONNECT_DELAY)
  }

  /**
   * Register a message handler for specific event type
   * @param {string} eventType - Event type to listen for
   * @param {Function} handler - Handler function
   */
  on(eventType, handler) {
    if (!this.messageHandlers.has(eventType)) {
      this.messageHandlers.set(eventType, [])
    }
    this.messageHandlers.get(eventType).push(handler)
    console.log(`[WebSocket] Registered handler for event: ${eventType}`)
  }

  /**
   * Unregister a message handler
   * @param {string} eventType - Event type
   * @param {Function} handler - Handler function to remove
   */
  off(eventType, handler) {
    if (this.messageHandlers.has(eventType)) {
      const handlers = this.messageHandlers.get(eventType)
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
        console.log(`[WebSocket] Unregistered handler for event: ${eventType}`)
      }
    }
  }

  /**
   * Handle incoming WebSocket message
   * @param {Object} message - Parsed message object
   */
  handleMessage(message) {
    const { type } = message

    if (!type) {
      console.warn('[WebSocket] Message missing type field:', message)
      return
    }

    // Call all registered handlers for this event type
    if (this.messageHandlers.has(type)) {
      const handlers = this.messageHandlers.get(type)
      handlers.forEach((handler) => {
        try {
          handler(message)
        } catch (error) {
          console.error(`[WebSocket] Handler error for ${type}:`, error)
        }
      })
    }

    // Also call handlers registered for 'all' events
    if (this.messageHandlers.has('*')) {
      const handlers = this.messageHandlers.get('*')
      handlers.forEach((handler) => {
        try {
          handler(message)
        } catch (error) {
          console.error('[WebSocket] Universal handler error:', error)
        }
      })
    }
  }

  /**
   * Send a message to the server
   * @param {Object} message - Message to send
   */
  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
      console.log('[WebSocket] Message sent:', message)
    } else {
      console.warn('[WebSocket] Cannot send message - not connected')
    }
  }

  /**
   * Check if connected
   * @returns {boolean}
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN
  }
}

// Export singleton instance
export const wsClient = new WebSocketClient()

// Export class for testing
export default WebSocketClient
