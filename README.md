# COGAR_Assignment_2026
# Subgroup F2: Gesture‑to‑Language‑to‑Action Robot Interface

## Assignment 2: LLM‑Driven Gesture Interpretation for Robot Teleoperation (EXPERIMENT + SIMULATION)

What to do: Create a novel gesture‑to‑language‑to‑action pipeline where hand gestures captured by MANUS Quantum Metagloves are classified, described in natural language via templates, interpreted by a Large Language Model, and converted into executable robot commands
1) Build a real‑time data acquisition node that streams MANUS Quantum Metagloves finger joint data (positions, angles, velocities) into a processing pipeline
2) Define a gesture vocabulary (10–15 gestures: point, pinch, grasp, release, wave, etc.) and collect a small labeled dataset (~500 samples)
3) Train a lightweight gesture classifier (LSTM or 1D‑CNN) on the collected dataset
4) Develop a template‑based Gesture‑to‑Language module that converts classified gesture sequences into structured natural language descriptions
5) Integrate an LLM (GPT‑4 / LLaMA / Mistral) that receives gesture descriptions + scene context and outputs structured robot action plans
6) Connect the action plan output to a robot controller via ROS2 (simulated in Gazebo)
7) Evaluate the full pipeline: gesture classification accuracy, LLM command correctness, end‑to‑end task success rate
8) Compare against a baseline direct‑mapping teleoperation system (gesture → joint angles, no LLM)

Software needed: MANUS Core SDK, Python, PyTorch, ROS2 Humble, Gazebo, LLM API (OpenAI / local LLaMA), MoveIt2

Research needed: VLA (Vision‑Language‑Action) models, gesture classification methods, LLM grounding for robotics (SayCan, Code‑as‑Policies, RT‑2), human grasp taxonomy (Feix et al.)

Deliverables: Gesture classifier trained model, template‑based language module, LLM integration node for ROS2, full evaluation report with ablation study
