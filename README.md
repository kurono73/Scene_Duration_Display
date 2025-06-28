#Blender Addon: Scene　Duration　Display
This Blender add-on adds an interactive "Duration" field to the header of the Timeline.

### Main Features
* **Interactive Duration Display**:
    * Shows the length of the current frame range in frames.
    * Automatically switches between displaying the duration of the main timeline range and the preview range when "Use Preview Range" is toggled.
* **Bidirectional Sync**:
    * The Duration field updates in real-time when you change the Start/End frames.
    * Conversely, editing the Duration value automatically updates the corresponding End Frame.
* **Intuitive I/O Buttons**:
    * **`I<` Button**: Sets the current playhead frame as the **In-point (Preview Start)** of the preview range. This also automatically enables "Use Preview Range".
    * **`>O` Button**: Sets the current playhead frame as the **Out-point (Preview End)** of the preview range.

#### How to Use
1.  **Locating the UI**:
    Find the new `I< [Duration] >O` controls in the header of the Timeline.

2.  **Setting the Preview Range (I/O Method)**:
    1.  Move the playhead to your desired **start frame**.
    2.  Click the `I<` button. This sets the Preview Start.
    3.  Move the playhead to your desired **end frame**.
    4.  Click the `>O` button. This sets the Preview End, and the duration between them will be calculated and displayed instantly.

3.  **Editing Duration Directly**:
    * Click the numerical field between the `I<` and `>O` buttons.
    * Type a new duration and press `Enter`.
    * The End Frame (or Preview End Frame, depending on the current mode) will be adjusted accordingly.
