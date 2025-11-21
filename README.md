# 🏎️ Mental Fatigue Propagation in Racing  
### Cognitive Load Index (CLI) + Track Heatmap for GR Cup — HackTheTrack 2025

This project analyzes GR Cup telemetry to estimate a driver’s **moment-to-moment cognitive load** throughout a lap.  
Using steering entropy, throttle instability, and brake violence, the system computes a **Cognitive Load Index (CLI)** and visualizes it on a reconstructed track map.

The result is a tool that reveals:
- Where the driver is mentally overloaded ⚠️  
- Where hesitation or panic inputs occur  
- Which corners require training or setup adjustment  
- How mental load affects lap performance  

This project fits the **Driver Training & Insights** category of HackTheTrack.

---

# 🚀 Features

### ✔ Cognitive Load Index (CLI)
A composite metric built from:
- Steering Entropy  
- Throttle Jerk  
- Brake Panic Spikes  

Computed on a rolling 0.5s window.

---

### ✔ Track Map Heatmap
A smoothed, rotated dead-reckoning track reconstruction colored by cognitive load:
- Blue → low mental effort  
- Red → overload / hesitation / instability  

Shows exactly where the driver struggles most.

---

### ✔ CLI vs Distance Graph
A clean signal visualization for:
- peak stress regions  
- straight-line mental fatigue  
- braking zone overload  

---

### ✔ Insights Engine
Generates:
- Top 5 highest-stress segments  
- Top 5 lowest-stress segments  
- Underlying causes (steering vs throttle vs brake)  
- Corners linked to performance loss  

---

### ✔ Interactive Streamlit Dashboard
Run the entire system with:

