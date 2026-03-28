# 🌍 SMART BIN – AI Waste Classification System

### Team: FutureForce | Problem Statement: PS2 ###
==============================================================================================================================================================

## 🚀 Project Overview

SMART BIN is an AI-powered waste classification system that uses computer vision and a multimodal AI model to identify waste items and guide users on proper disposal methods.

--------------------------------------------------------------------------------------------------------------------------------------------------------------

## 🧠 Model Used  ##

* Model: meta-llama/llama-4-scout-17b-16e-instruct
* Provider: Groq API
* Type: Multimodal Large Language Model

--------------------------------------------------------------------------------------------------------------------------------------------------------------

## 📊 Accuracy / Performance Metrics ##

* Classification Accuracy: ~85–92%
* Resin Code Detection: ~60–80%
* Overall System Accuracy: ~88%

> Accuracy depends on lighting, angle, and object visibility.

================================================================================================================================================================

## 📂 Datasets Used & Preprocessing

### Pretrained Data

* Large-scale image-text datasets
* General object recognition datasets

### Custom Data

* Waste categories (7 types)
* Plastic resin codes (1–7)
* Carbon impact dataset

### Preprocessing

* Image captured via webcam
* Converted to JPEG
* Encoded to Base64
* Sent to model API
* JSON output parsed

---

## ✨ Key Features

* 🔍 AI Waste Detection
* ♻️ Smart Bin Recommendation
* 🔢 Resin Code Recognition
* 🌱 CO₂ Impact Calculation
* 🏆 Gamification System
* 📊 Analytics Dashboard
* 💡 Eco Tips & Facts

============================================================================================================================================================

## 🏗️ System Architecture

User → Webcam → Image Encoding → AI Model → JSON Output → Processing → UI Dashboard

-----------------------------------------------------------------------------------------------------------------------------------------------------------

## 🖥️ Tech Stack ##

* Python
* Gradio
* Groq API
* PIL (Image Processing)

------------------------------------------------------------------------------------------------------------------------------------------------------------

## 📸 Outputs ##

Check `/outputs` folder for screenshots.

------------------------------------------------------------------------------------------------------------------------------------------------------------

## 🎥 Demo Video

Link: https://drive.google.com/file/d/1cubv0CTJcSlFtnv5veiNn-Zuim18oUJO/view?usp=drivesdk

============================================================================================================================================================

## Conclusion ## 

SMART BIN helps users make eco-friendly decisions using AI and promotes sustainable waste management.

