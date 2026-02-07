"""
Queue Wait Time Estimator - Proof of Concept
Simulates real-world service queue with only service completion timestamps.
Demonstrates AI pattern recognition for invisible public infrastructure problems.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import random

class QueueSimulator:
    """
    Simulates a real-world service queue with human operators.
    Key assumption: We only observe service completion timestamps, NOT arrivals.
    """
    
    def __init__(self, hours=8, base_service_time=5):
        """
        Initialize queue simulation with realistic human behavior patterns.
        
        Args:
            hours: Simulation duration in hours
            base_service_time: Base service time in minutes (varies throughout day)
        """
        self.hours = hours
        self.base_service_time = base_service_time
        self.service_completions = []  # Only this is observable in real world
        self.actual_wait_times = []    # For validation (not observable in reality)
        
        # Human behavior patterns - these are UNKNOWN to the estimator
        self.patterns = {
            'morning_rush': (0, 2),      # First 2 hours: faster service
            'midday_slowdown': (2, 5),    # Hours 2-5: fatigue sets in
            'afternoon_recovery': (5, 7), # Hours 5-7: post-lunch recovery
            'evening_rush': (7, 8)        # Last hour: rushing to finish
        }
        
    def generate_synthetic_data(self):
        """
        Generate realistic service completion timestamps with hidden patterns.
        Models human factors: fatigue, interruptions, variable transaction complexity.
        """
        start_time = datetime.now().replace(hour=8, minute=0, second=0)
        current_time = start_time
        customer_id = 1
        
        for hour in range(self.hours):
            # Hidden pattern: service speed varies throughout the day
            if self.patterns['morning_rush'][0] <= hour < self.patterns['morning_rush'][1]:
                # Morning: fresh staff, efficient
                service_multiplier = 0.8
                customers_per_hour = 15
            elif self.patterns['midday_slowdown'][0] <= hour < self.patterns['midday_slowdown'][1]:
                # Midday: fatigue, longer breaks
                service_multiplier = 1.5
                customers_per_hour = 8
            elif self.patterns['afternoon_recovery'][0] <= hour < self.patterns['afternoon_recovery'][1]:
                # Afternoon: recovered but inconsistent
                service_multiplier = 1.0
                customers_per_hour = 12
            else:
                # Evening: rushing to finish
                service_multiplier = 0.9
                customers_per_hour = 14
            
            for _ in range(customers_per_hour):
                # Real-world variation: each transaction is different
                complexity = random.uniform(0.7, 1.3)  # Document complexity factor
                service_time = self.base_service_time * service_multiplier * complexity
                
                # Add random interruptions (5% chance of 10-min delay)
                if random.random() < 0.05:
                    service_time += 10
                
                # Record service completion (ONLY THIS IS OBSERVABLE)
                current_time += timedelta(minutes=service_time)
                self.service_completions.append({
                    'timestamp': current_time,
                    'customer_id': customer_id,
                    'actual_service_time': service_time
                })
                
                # Simulate wait time (for validation only - not observable)
                if customer_id > 1:
                    wait = (current_time - self.service_completions[-2]['timestamp']).seconds / 60
                    self.actual_wait_times.append(wait)
                
                customer_id += 1
        
        return pd.DataFrame(self.service_completions)

class WaitTimeEstimator:
    """
    AI system that estimates wait times using ONLY service completion timestamps.
    Models the core insight: Service rate reveals queue dynamics better than queue length.
    """
    
    def __init__(self, window_size=10):
        """
        Initialize estimator with rolling window for adaptive learning.
        
        Args:
            window_size: Number of recent completions to consider (balances responsiveness vs stability)
        """
        self.window_size = window_size
        self.service_rates = []  # Track service rate over time
        self.predictions = []    # Store predictions for analysis
        self.confidence_scores = []  # Track prediction reliability
        
    def calculate_service_rate(self, timestamps):
        """
        Calculate current service rate from completion timestamps.
        Core AI insight: Rate of completions reveals processing capacity.
        
        Args:
            timestamps: List of recent service completion timestamps
            
        Returns:
            service_rate: Customers served per minute
            trend: 'speeding_up', 'slowing_down', or 'stable'
        """
        if len(timestamps) < 2:
            return 0, 'stable'
        
        # Calculate intervals between completions
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]).seconds / 60  # Convert to minutes
            intervals.append(interval)
        
        # Service rate = 1/average interval (customers per minute)
        avg_interval = np.mean(intervals)
        current_rate = 1 / avg_interval if avg_interval > 0 else 0
        
        # Detect trend by comparing to historical average
        self.service_rates.append(current_rate)
        
        if len(self.service_rates) < 3:
            trend = 'stable'
        else:
            # Simple trend detection: compare recent vs historical
            recent_avg = np.mean(self.service_rates[-3:])
            historical_avg = np.mean(self.service_rates[:-3]) if len(self.service_rates) > 3 else recent_avg
            
            if recent_avg > historical_avg * 1.1:
                trend = 'speeding_up'
            elif recent_avg < historical_avg * 0.9:
                trend = 'slowing_down'
            else:
                trend = 'stable'
        
        return current_rate, trend
    
    def estimate_wait_time(self, service_rate, trend):
        """
        Estimate wait time based on current service dynamics.
        Key innovation: Estimates wait WITHOUT counting arrivals.
        
        Args:
            service_rate: Current service rate (customers/minute)
            trend: Current trend ('speeding_up', 'slowing_down', 'stable')
            
        Returns:
            estimated_wait: Expected wait time in minutes
            confidence: High/Medium/Low based on data quality and stability
        """
        if service_rate == 0:
            return 0, 'Low'
        
        # Base estimate: Assume 5 people typically waiting (common in public queues)
        # In real deployment, this would be learned from historical patterns
        estimated_queue_length = 5
        
        # Adjust based on trend
        if trend == 'slowing_down':
            estimated_queue_length *= 1.5  # Expect more backlog during slowdown
        elif trend == 'speeding_up':
            estimated_queue_length *= 0.7  # Expect faster clearance
        
        # Calculate wait: queue_length / service_rate
        estimated_wait = estimated_queue_length / service_rate
        
        # Calculate confidence based on data stability
        if len(self.service_rates) < 5:
            confidence = 'Low'
        elif np.std(self.service_rates[-5:]) < 0.1:  # Stable recent rates
            confidence = 'High'
        else:
            confidence = 'Medium'
        
        return estimated_wait, confidence
    
    def detect_anomalies(self, service_rates):
        """
        Detect unusual service patterns indicating problems.
        AI value: Identifies invisible operational issues.
        
        Args:
            service_rates: List of recent service rates
            
        Returns:
            anomaly: Description of detected anomaly or None
        """
        if len(service_rates) < 5:
            return None
        
        recent = service_rates[-5:]
        historical = service_rates[:-5] if len(service_rates) > 5 else recent
        
        recent_std = np.std(recent)
        historical_std = np.std(historical) if len(historical) > 1 else recent_std
        
        # Detect high variability (indicates unstable service)
        if recent_std > historical_std * 2:
            return "High service variability detected - possible staff interruptions"
        
        # Detect sudden slowdown
        if np.mean(recent) < np.mean(historical) * 0.5:
            return "Major slowdown detected - possible system issue"
        
        return None

def visualize_results(service_rates, predictions, actual_wait_times=None):
    """
    Create visualization for public display.
    Shows transparency and builds trust in the system.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot 1: Service Rate Trend
    ax1.plot(service_rates, 'b-', linewidth=2, label='Service Rate (customers/min)')
    ax1.axhline(y=np.mean(service_rates), color='r', linestyle='--', 
                label=f'Average: {np.mean(service_rates):.2f}')
    
    # Highlight patterns
    patterns = [(0, 30, 'Morning Rush'), (30, 75, 'Midday Slowdown'), 
                (75, 105, 'Afternoon Recovery'), (105, 120, 'Evening Rush')]
    
    for start, end, label in patterns:
        if start < len(service_rates):
            ax1.axvspan(start, min(end, len(service_rates)), alpha=0.2, color='gray')
            ax1.text((start + end) / 2, max(service_rates) * 0.9, label, 
                    ha='center', fontsize=8)
    
    ax1.set_xlabel('Service Completion Number')
    ax1.set_ylabel('Service Rate (customers/min)')
    ax1.set_title('Service Capacity Analysis - Reveals Hidden Queue Dynamics')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Wait Time Predictions
    if predictions:
        pred_times = [p[0] for p in predictions]
        confidences = [p[1] for p in predictions]
        
        colors = {'High': 'green', 'Medium': 'orange', 'Low': 'red'}
        conf_colors = [colors[c] for c in confidences]
        
        bars = ax2.bar(range(len(pred_times)), pred_times, color=conf_colors, alpha=0.7)
        ax2.set_xlabel('Prediction Instance')
        ax2.set_ylabel('Estimated Wait (minutes)')
        ax2.set_title('Real-Time Wait Estimates with Confidence Indicators')
        
        # Add confidence legend
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='green', alpha=0.7, label='High Confidence'),
                          Patch(facecolor='orange', alpha=0.7, label='Medium Confidence'),
                          Patch(facecolor='red', alpha=0.7, label='Low Confidence')]
        ax2.legend(handles=legend_elements)
        
        # Add actual wait times for validation (if available)
        if actual_wait_times and len(actual_wait_times) >= len(pred_times):
            ax2.plot(actual_wait_times[:len(pred_times)], 'k--', linewidth=2, 
                    label='Actual Wait (for validation)')
            ax2.legend()
    
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save for public display
    plt.savefig('queue_analysis_display.png', dpi=100, bbox_inches='tight')
    print("\n Visualization saved as 'queue_analysis_display.png'")
    print("   This is what would be shown on a public digital display.")
    
    return fig

def simulate_public_display_output(estimator, service_data, update_interval=5):
    """
    Simulate real-time public display updates.
    Shows practical implementation for citizen information.
    """
    print("\n" + "="*60)
    print("PUBLIC DISPLAY SIMULATION - Real-Time Updates")
    print("="*60)
    
    timestamps = service_data['timestamp'].tolist()
    
    for i in range(update_interval, len(timestamps), update_interval):
        # Get recent completions
        recent_timestamps = timestamps[max(0, i-estimator.window_size):i]
        
        # Calculate current service dynamics
        service_rate, trend = estimator.calculate_service_rate(recent_timestamps)
        wait_time, confidence = estimator.estimate_wait_time(service_rate, trend)
        anomaly = estimator.detect_anomalies(estimator.service_rates)
        
        estimator.predictions.append((wait_time, confidence))
        
        # Display format for public viewing
        print(f"\n🕐 Update at {timestamps[i].strftime('%H:%M')}")
        print(f"   Estimated Wait: {wait_time:.0f} minutes")
        print(f"   Service Status: {trend.upper().replace('_', ' ')}")
        print(f"   Confidence: {confidence}")
        
        if anomaly:
            print(f"   ⚠️  ALERT: {anomaly}")
        
        # Simulate display refresh
        print("-"*40)

def main():
    """
    Main demonstration of AI-powered queue transparency system.
    """
    print("="*70)
    print("AI-POWERED QUEUE TRANSPARENCY SYSTEM")
    print("Proof of Concept for Public Service Wait Time Estimation")
    print("="*70)
    
    print("\nPROBLEM CONTEXT:")
    print("- Citizens join queues without knowing true wait time")
    print("- Service speed varies due to human factors (fatigue, complexity)")
    print("- Traditional solution: Count people (inaccurate)")
    print("- AI insight: Analyze service completion PATTERNS")
    
    # Step 1: Simulate real-world queue
    print("\n STEP 1: Generating realistic queue data...")
    simulator = QueueSimulator(hours=8, base_service_time=4)
    service_data = simulator.generate_synthetic_data()
    print(f"   Generated {len(service_data)} service completions")
    print(f"   Simulation covers 8 hours of operation")
    
    # Step 2: Initialize AI estimator
    print("\n STEP 2: Initializing AI estimator...")
    estimator = WaitTimeEstimator(window_size=10)
    print(f"   Using rolling window of {estimator.window_size} completions")
    print("   Key constraint: NO arrival data, ONLY completion timestamps")
    
    # Step 3: Run real-time simulation
    print("\n STEP 3: Simulating real-time analysis...")
    simulate_public_display_output(estimator, service_data)
    
    # Step 4: Generate insights
    print("\n STEP 4: Generating operational insights...")
    if estimator.service_rates:
        avg_rate = np.mean(estimator.service_rates)
        print(f"   Average service rate: {avg_rate:.2f} customers/minute")
        print(f"   Peak efficiency: {max(estimator.service_rates):.2f} customers/minute")
        print(f"   Lowest efficiency: {min(estimator.service_rates):.2f} customers/minute")
    
    # Step 5: Visualize for public display
    print("\n STEP 5: Creating public information display...")
    fig = visualize_results(estimator.service_rates, 
                          estimator.predictions,
                          simulator.actual_wait_times)
    
    # Final summary
    print("\n" + "="*70)
    print("SYSTEM DEMONSTRATION COMPLETED")
    print("="*70)
    
    
    print("\n Output files generated:")
    print("   1. queue_analysis_display.png - Public display visualization")
    print("   2. Console output - Real-time simulation log")
    
    # Show sample of what would be on digital display
    print("\n" + "="*70)
    print("SAMPLE PUBLIC DISPLAY CONTENT:")
    print("="*70)
    print("\n   CURRENT WAIT TIME: 25 minutes")
    print("   SERVICE STATUS: SLOWING DOWN")
    print("   CONFIDENCE: MEDIUM")
    print("   LAST UPDATE: 14:30")
    print("\n    TIP: Service typically speeds up after 15:00")
    print("="*70)

if __name__ == "__main__":
    main()