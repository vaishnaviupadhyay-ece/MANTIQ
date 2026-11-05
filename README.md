# MANTIQ — Action Before Failure

### AI-Assisted Industrial Condition Monitoring & Maintenance Management

**Turning machine-condition anomalies into actionable, traceable and verifiable maintenance decisions.**

MANTIQ is an AI-assisted industrial maintenance platform designed to help manufacturing facilities and warehouses monitor rotating machinery, identify unusual bearing behaviour, and coordinate maintenance actions through a structured, role-based workflow.

Rather than presenting anomaly scores as isolated technical readings, MANTIQ connects condition monitoring with the people responsible for responding to equipment issues.

It brings together machine-condition analysis, prioritised alerts, operator observations, maintenance assignments, resolution records and verification into one platform.

> **Action Before Failure.**

---

## 1. The Problem

Industrial equipment rarely fails without warning. Changes in vibration behaviour and other operating signals can indicate developing abnormalities. However, identifying unusual behaviour is only one part of the maintenance problem.

In many industrial environments, the response process can be fragmented:

- Machine-condition information is difficult for operators to interpret.
- Anomalies may not translate into clear maintenance priorities.
- Operator observations can be disconnected from maintenance decisions.
- Escalation and assignment processes may lack traceability.
- Resolution does not necessarily guarantee that the issue has been verified.
- Maintenance teams may lack a consolidated record of actions taken.

The result is a gap between **detecting an abnormal condition and ensuring that someone acts on it.**

## 2. Our Solution

MANTIQ bridges this gap through an integrated condition-monitoring and maintenance workflow.

The platform analyses historical bearing vibration data using machine-learning models, converts anomaly outputs into simplified condition categories, and connects those categories to a structured maintenance process.

### The MANTIQ approach

1. **Monitor:** Analyse vibration-derived features for individual bearings.
2. **Identify:** Use Isolation Forest models to flag unusual operating patterns.
3. **Prioritise:** Translate model outputs into Normal, Warning and Critical condition categories using prototype heuristic rules.
4. **Communicate:** Allow operators to acknowledge alerts, document observations and escalate concerns.
5. **Coordinate:** Enable Maintenance Heads to assign work and record corrective actions.
6. **Verify:** Maintain a final verification step and an auditable activity history.

MANTIQ is designed around a simple principle: an anomaly should lead to an accountable maintenance response, not remain an isolated data point.

---

## 3. Key Features

### AI-Assisted Bearing Condition Monitoring

- Individual Isolation Forest models for four bearings.
- Statistical vibration-feature extraction.
- Anomaly scores and anomaly flags.
- Per-bearing condition assessment.
- Historical condition trends and anomaly-rate visualisations.
- Experimental historical-data replay.

### Role-Based Dashboards

**Operator Dashboard**
- Overall machine-condition summary.
- Individual bearing health.
- Condition trends.
- Recent maintenance alerts.
- Operator findings and escalation workflow.
- Maintenance activity visibility.

**Maintenance Head Dashboard**
- Maintenance workload overview.
- Pending acknowledgements.
- Unassigned maintenance work.
- Active maintenance tasks.
- Pending verification.
- Components requiring attention.
- Maintenance activity history.

### Structured Alert Management

Every maintenance alert follows a defined lifecycle:

`NEW → ACKNOWLEDGED → UNDER MAINTENANCE → RESOLVED → VERIFIED`

The workflow supports:

- Alert acknowledgement.
- Operator findings.
- Escalation to the Maintenance Head.
- Maintenance assignment.
- Corrective-action recording.
- Final verification.
- Chronological activity logging.

### Traceability and Accountability

MANTIQ maintains a record of maintenance events, including:

- Who performed an action.
- The action performed.
- The associated alert.
- The time of the action.
- Relevant findings or maintenance details.

This creates a traceable link between an identified condition and the subsequent maintenance response.

### Historical Data Replay

The replay functionality allows users to explore the historical dataset and observe how model outputs and condition assessments change across recordings.

It supports demonstrations and examination of the model's behaviour without implying that a live factory sensor connection is currently deployed.

---

## 4. Technical Architecture

MANTIQ follows a modular Python application architecture that separates machine-learning processing, application services, database operations and user-interface components.

```text
                  MANTIQ PLATFORM
                         |
          +--------------+--------------+
          |                             |
     DATA PIPELINE                USER INTERFACE
          |                             |
   NASA IMS Dataset             Role-Based Access
          |                             |
   Feature Extraction       +-----------+-----------+
          |                 |                       |
   Per-Bearing ML       Operator Dashboard    Maintenance Head
          |                 |                  Dashboard
   Anomaly Scoring          |                       |
          |                 +-----------+-----------+
   Condition Engine                     |
          |                      Alert Management
   Condition Assessment                 |
          |                      SQLite Database
   Historical Trends                   |
          +----------------------------+
                         |
                Activity and History
```

### Application modules

| Module | Responsibility |
|---|---|
| `src/` | Data processing, feature extraction and model development |
| `app/pages/` | Operator and Maintenance Head dashboards |
| `app/components/` | Reusable interface elements, charts and visual components |
| `app/services/` | Authentication, condition assessment, replay and application services |
| `app/database/` | Alert management and maintenance activity persistence |
| `models/` | Trained per-bearing model artifacts |
| `data/processed/` | Processed vibration-feature dataset |
| `assets/` | Branding and presentation assets |

The modular structure supports future integration of additional machine types, sensor sources and maintenance workflows without requiring the entire application to be redesigned.

---

## 5. Machine Learning Methodology

### Dataset

The current prototype uses the **NASA IMS Bearing Dataset**, a publicly available experimental dataset for bearing condition monitoring.

The selected experimental recording set contains:

| Dataset characteristic | Value |
|---|---:|
| Number of recordings | 2,156 |
| Samples per recording and channel | 20,480 |
| Number of channels | 8 |
| Number of bearings | 4 |
| Sampling frequency | 20 kHz |
| Recording interval | 1 second |

Two vibration channels are associated with each bearing.

The experiment records bearing degradation under controlled test conditions. The dataset provides a useful foundation for exploring anomaly detection in rotating machinery.

### Feature Engineering

The raw vibration recordings are transformed into statistical features.

Five features are extracted from each channel:

1. Root Mean Square (RMS)
2. Standard Deviation
3. Peak Absolute Amplitude
4. Kurtosis
5. Crest Factor

With eight channels and five features per channel, the processed dataset contains **40 features per recording**, in addition to its timestamp.

This feature representation provides a compact numerical description of vibration behaviour for downstream anomaly detection.

### Model Development

MANTIQ uses an individual Isolation Forest model for each bearing.

| Parameter | Configuration |
|---|---|
| Algorithm | Isolation Forest |
| Models | One per bearing |
| Estimators | 200 |
| Contamination setting | 0.05 |
| Random state | 42 |
| Training split | First 60% |
| Testing split | Remaining 40% |
| Feature scaling | Standardisation |
| Missing-value handling | Training-set medians |

The dataset is divided chronologically rather than randomly:

- The first 60% of recordings are used for training.
- The remaining 40% are reserved for testing.
- Imputation values and scaling parameters are fitted on training data only.

This approach preserves temporal ordering and helps avoid information leakage from the later test period into model fitting.

### Anomaly Scoring

Each model generates:

- An anomaly score using the Isolation Forest decision function.
- An anomaly flag using the model's prediction output.

Lower decision-function scores indicate more unusual observations. A negative score is classified as an anomaly by the model.

The model outputs are used as inputs to MANTIQ's condition-assessment layer.

### Condition Assessment

MANTIQ translates anomaly outputs into three simplified condition categories:

| Condition | Meaning |
|---|---|
| NORMAL | No elevated concern under the current prototype rules |
| WARNING | Unusual behaviour warrants closer monitoring or inspection |
| CRITICAL | Elevated concern warrants maintenance attention |

The condition engine considers anomaly rate, average anomaly score and consecutive anomaly flags over a rolling window of up to 50 recordings.

**Important:** These condition categories are prototype heuristic assessments. They are not validated industrial operating limits, confirmed fault diagnoses or estimates of remaining useful life.

---

## 6. Industrial Relevance and Potential Impact

MANTIQ is designed to address the operational gap between condition monitoring and maintenance execution.

Its potential applications include:

- Manufacturing facilities.
- Automotive and automotive-component production.
- Industrial warehouses.
- Rotating machinery and bearing monitoring.
- Equipment maintenance teams.

### What makes MANTIQ different?

The innovation is not simply the use of an anomaly-detection algorithm.

MANTIQ integrates machine-learning outputs with a human-centred maintenance process:

- Machine-level anomalies are organised into understandable condition categories.
- Operators can contribute contextual observations.
- Maintenance Heads can assign and track corrective actions.
- Verification creates an additional accountability step.
- Activity records preserve the history of maintenance decisions.

This combination makes MANTIQ a maintenance coordination platform built around condition intelligence, rather than a standalone anomaly visualisation dashboard.

---

## 7. Technology Stack

| Technology | Application |
|---|---|
| Python | Core application and ML development |
| Streamlit | Interactive web application |
| NumPy | Numerical processing |
| Pandas | Dataset processing and analysis |
| SciPy | Statistical signal processing |
| Scikit-learn | Isolation Forest and feature scaling |
| Plotly | Interactive data visualisations |
| SQLite | Alert and maintenance data persistence |
| Joblib | Model serialisation and loading |
| HTML/CSS | Interface styling and theme customisation |
| Git and GitHub | Version control and project hosting |

---

## 8. Project Screenshots

### Operator Dashboard

The operator interface provides a consolidated view of bearing condition, anomaly trends and maintenance activity.

![Operator Dashboard](assets/screenshots/operator-dashboard.png)

### Maintenance Head Dashboard

The Maintenance Head interface focuses on workload, maintenance priorities and verification.

![Maintenance Head Dashboard](assets/screenshots/maintenance-dashboard.png)

### Historical Replay

Historical replay allows users to examine condition assessments across the experimental dataset.

![Historical Replay](assets/screenshots/replay.png)

### Alert Management

The alert interface supports acknowledgement, operator findings, escalation and maintenance coordination.

![Alert Management](assets/screenshots/alerts.png)

---

## 9. Installation and Setup

### Prerequisites

- Python 3.11 recommended.
- Git.
- pip.
- Windows, Linux or macOS.

### Step 1: Clone the repository

```bash
git clone https://github.com/vaishnaviupadhyay-ece/MANTIQ.git

cd MANTIQ
```

### Step 2: Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv

.venv\Scripts\Activate.ps1
```

**Linux / macOS**

```bash
python3 -m venv .venv

source .venv/bin/activate
```

### Step 3: Install dependencies

```bash
python -m pip install --upgrade pip

pip install -r requirements.txt
```

### Step 4: Obtain the NASA IMS dataset

The raw NASA IMS dataset is not included in this repository because of its large file size.

Download it from:

[Download NASA IMS Bearing Dataset](https://phm-datasets.s3.amazonaws.com/NASA/4.+Bearings.zip)

Extract the required `1st_test` recording directory into:

```text
data/raw/IMS/IMS/1st_test/
```

The repository includes the processed feature dataset and trained model artifacts. If you want to regenerate the pipeline from raw recordings, ensure the raw dataset is extracted into the expected location.

### Step 5: Run MANTIQ

```bash
streamlit run app/main.py
```

Open the local URL displayed in the terminal to access the application.

Use the demo accounts configured for the Operator and Maintenance Head roles.

---

## 10. Demo and Presentation

**Project demonstration:** [Insert your demo video link here]

The demonstration covers:

1. MANTIQ login and role-based access.
2. Operator dashboard and bearing-condition overview.
3. Anomaly trends and historical data replay.
4. Alert acknowledgement and operator findings.
5. Escalation to the Maintenance Head.
6. Maintenance assignment and corrective-action recording.
7. Resolution verification and activity history.

The demonstration uses historical experimental data and the application's simulated replay workflow.

---

## 11. Limitations and Responsible Interpretation

MANTIQ is a working prototype developed using historical experimental bearing data.

The following distinctions are important:

- The current prototype uses the NASA IMS dataset, not a live factory sensor feed.
- Isolation Forest flags unusual patterns; it does not independently confirm a mechanical fault.
- Condition thresholds are heuristic prototype rules, not validated industrial standards.
- The current implementation does not establish guaranteed failure-prediction lead times or remaining useful life.
- The alert workflow demonstrates software-based maintenance coordination; it does not directly control industrial equipment.
- Demo authentication is not intended to represent production-grade enterprise security.

These boundaries define the current implementation and the next engineering challenges.

---

## 12. Future Scope and Scalability

MANTIQ is envisioned as a modular condition-intelligence and maintenance ecosystem that can expand beyond the current experimental bearing-monitoring prototype.

### Multi-Asset and Multi-Sensor Integration

Support additional rotating machinery and configurable sensor combinations, allowing the platform to be adapted to different industrial assets.

### Edge-Based Monitoring

Introduce edge gateways capable of processing vibration and other sensor measurements closer to the equipment, reducing dependence on continuous cloud connectivity.

### Configurable Asset Profiles

Allow facilities to configure machine-specific operating parameters, sensor combinations and condition-assessment rules rather than relying on a single universal threshold.

### Advanced Predictive Analytics

Explore temporal models, fault classification, degradation modelling and remaining-useful-life estimation using appropriately labelled and validated datasets.

### Industrial Connectivity

Investigate integration with industrial communication protocols, MQTT-based data pipelines and existing maintenance management systems.

### Multilingual Operator Assistance

Extend concise maintenance instructions and operational guidance across English, Hindi and Kannada, with optional text-to-speech support.

### Enterprise Deployment

Develop stronger authentication, access control, auditability, multi-facility support and scalable time-series data storage.

**Long-term vision:** A configurable industrial maintenance platform that connects sensor intelligence, machine-level insights and accountable human action across different facilities and equipment types.

---

## 13. AI Tools and Development Assistance

AI-assisted tools were used during the development of MANTIQ:

- **ChatGPT (OpenAI):** Architecture discussions, coding assistance, debugging, implementation guidance and technical documentation.
- **Claude (Anthropic):** Coding assistance, code review, debugging and development support.

AI tools supported the development process. Implementation, integration, testing, model development and review were part of the project development workflow.

---

## 14. Project Information

| Detail | Information |
|---|---|
| Project | MANTIQ |
| Domain | AI/ML, Industrial IoT and Predictive Maintenance |
| Application | Industrial condition monitoring and maintenance management |
| ML algorithm | Isolation Forest |
| Dataset | NASA IMS Bearing Dataset |
| Development language | Python |
| Repository | [GitHub – MANTIQ](https://github.com/vaishnaviupadhyay-ece/MANTIQ) |
| Tagline | Action Before Failure |

---

**MANTIQ — Action Before Failure.**

*From machine-condition intelligence to accountable maintenance action.*