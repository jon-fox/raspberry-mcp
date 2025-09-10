import asyncio
import RPi.GPIO as GPIO
from datetime import datetime

class IRListenerManager:
    """Manages the background IR listener process."""
    
    _instance = None
    _listener_task = None
    _ir_events = []
    _is_listening = False
    PIN = 27  # GPIO27 (pin 13)
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        return cls()
    
    def is_listening(self) -> bool:
        return self._is_listening
    
    async def start_listening(self) -> tuple[bool, str]:
        """Start the IR listener in the background."""       
        if self._is_listening:
            return True, "IR listener is already running."
        
        try:
            # Initialize GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Start the listener task
            self._listener_task = asyncio.create_task(self._listen_loop())
            self._is_listening = True
            
            return True, "IR listener started successfully. Press remote buttons to capture signals."
            
        except Exception as e:
            return False, f"Failed to start IR listener: {str(e)}"
    
    async def stop_listening(self) -> tuple[bool, str]:
        """Stop the IR listener."""
        if not self._is_listening:
            return True, "IR listener is not running."
        
        try:
            self._is_listening = False
            
            if self._listener_task:
                self._listener_task.cancel()
                try:
                    await self._listener_task
                except asyncio.CancelledError:
                    pass
                self._listener_task = None
            
            GPIO.cleanup()
            
            return True, "IR listener stopped successfully."
            
        except Exception as e:
            return False, f"Failed to stop IR listener: {str(e)}"
    
    def get_recent_events(self, horizon_s: int = 20) -> list:
        """Get IR events from the last horizon_s seconds."""
        cutoff_time = datetime.now().timestamp() - horizon_s
        return [
            event for event in self._ir_events 
            if event['timestamp'].timestamp() > cutoff_time
        ]
    
    def clear_events(self):
        """Clear all recorded IR events."""
        self._ir_events.clear()
    
    async def _listen_loop(self):
        """Background loop that listens for IR signals."""
        try:
            while self._is_listening:
                if GPIO.input(self.PIN) == 0:  # active low
                    # Record IR event with timestamp
                    timestamp = datetime.now()
                    self._ir_events.append({
                        'timestamp': timestamp,
                        'type': 'button_press'
                    })
                    
                    # Wait for the signal to end
                    while GPIO.input(self.PIN) == 0 and self._is_listening:
                        await asyncio.sleep(0.001)
                
                # prevents complete blocking in loop
                await asyncio.sleep(0.01)  # Check every 10ms
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"IR listener error: {e}")
            self._is_listening = False
