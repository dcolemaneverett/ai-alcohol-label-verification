# AI-Powered Alcohol Label Verification Prototype

## Design Decisions and Requirements

### 1\. Project Objective

Build a standalone proof-of-concept that helps TTB compliance agents compare alcohol label information against application data.

The prototype should:

* Reduce routine manual comparison work
* Return useful results in approximately five seconds
* Be easy to use for agents with different levels of technical comfort
* Preserve human judgment for ambiguous cases
* Avoid unnecessary dependence on external APIs

### 2\. Primary Users

Primary user: TTB compliance agent

Secondary stakeholders:

* Compliance leadership
* IT administrators
* Future modernization/procurement teams

### 3\. Core Workflow

1. Agent uploads a label image.
2. Agent enters expected application data.
3. System extracts text from the label.
4. System compares extracted information to the application.
5. System returns Match, Needs Review, or Mismatch.
6. Agent makes the final determination.

### 4\. Core Functional Requirements

FR-01: Upload label image.
FR-02: Enter application data.
FR-03: Extract label text using OCR.
FR-04: Compare brand name.
FR-05: Compare class/type.
FR-06: Compare alcohol content.
FR-07: Compare net contents.
FR-08: Validate government warning.
FR-09: Return Match, Needs Review, or Mismatch.
FR-10: Show extracted evidence.
FR-11: Handle unreadable images without false approval.
FR-12: Display processing time.

### 5\. Nonfunctional Requirements

NFR-01: Target approximately five seconds or less for normal single-label processing.
NFR-02: Simple, low-training interface.
NFR-03: Uncertain results should trigger human review.
NFR-04: Prototype should not intentionally retain uploaded data.
NFR-05: Core processing should not depend on an external generative AI API.
NFR-06: Results should be explainable.
NFR-07: Validation logic should be separate from the user interface.

### 6\. Initial Architecture

User
|
Streamlit Interface
|
+--> Application Data
|
+--> Label Image
|
Image Processing
|
OCR
|
Extracted Text
|
Normalization
|
Validation Engine
|
Match / Needs Review / Mismatch
|
Human Review

### 7\. Initial Technology Choices

* Python
* Streamlit
* Tesseract OCR / pytesseract
* Pillow or OpenCV
* RapidFuzz
* Regular expressions

### 8\. Validation Strategy

Brand name: normalized/flexible comparison
Class/type: normalized/flexible comparison
ABV: structured numeric comparison
Net contents: numeric and unit normalization
Government warning: strict rule-based validation
Unreadable text: Needs Review

### 9\. Human Oversight

The prototype assists the compliance agent. It does not approve or reject regulatory applications.

### 10\. Out of Scope for MVP

* COLA integration
* Authentication
* Production deployment controls
* Regulatory approval decisions
* Multi-user case management
* Full batch processing
* Enterprise security authorization

### 11\. Initial Acceptance Criteria

* Exact matches return Match
* Capitalization/punctuation differences do not create false mismatches
* ABV mismatches are detected
* Missing warning is detected
* Poor image quality triggers Needs Review
* Processing time is displayed
* Errors are handled clearly

### 12\. Design Decision Log

#### Decision 001

Decision: Use local OCR for the prototype.
Reason: Government network restrictions may block external ML/API endpoints.
Trade-off: Local OCR may be less accurate on distorted images.
Future option: Evaluate approved cloud OCR services in a production environment.



\## Test Results



\### Test 001 - Initial Clean Label

\- Processing time: 0.59 seconds

\- Brand: Mismatch due to stylized OCR failure

\- Class/type: Match

\- ABV: Match

\- Net contents: Match

\- Warning: Match

\- Finding: Single-pass OCR did not reliably read decorative brand text.



\### Test 002 - Multi-Pass OCR

\- Processing time: 2.48 seconds

\- Brand: Mismatch

\- Class/type: Match

\- ABV: Match

\- Net contents: Match

\- Warning: Match

\- Finding: OCR coverage improved while remaining under the 5-second target.



\### Test 003 - Human Review for Ambiguous Brand

\- Processing time: 2.44 seconds

\- Brand: Needs Review

\- Class/type: Match

\- ABV: Match

\- Net contents: Match

\- Warning: Match

\- Finding: Partial OCR evidence is routed to human review instead of being forced into Match or Mismatch.



\### Test 004 - Incorrect Alcohol Content

\- Input change: Expected alcohol content changed from 45% to 40%.

\- Expected result: Alcohol Content = Mismatch

\- Actual result: Mismatch

\- Finding: Structured ABV comparison correctly identified a numeric discrepancy.



\### Test 005 - Incorrect Net Contents

\- Input change: Expected net contents changed from 750 mL to 1 L.

\- Expected result: Net Contents = Mismatch

\- Actual result: Mismatch

\- Finding: Structured net-contents validation correctly identified a quantity/unit discrepancy.



\### Test 006 - Incorrect Government Warning

\- Input: Label contained intentionally incorrect government warning language.

\- Expected result: Government Warning = Mismatch

\- Actual result: \[enter actual result]

\- Processing time: \[enter time]

\- Finding: The validator distinguished the presence of a warning heading from compliance with the required warning text.

