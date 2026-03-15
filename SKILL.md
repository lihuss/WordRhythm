# WordRhythm Automation Skill (Optimized for AI)

## 0. Hierarchy of Instructions (IMPORTANT)
**User Prompt Priority**: The specific requirements in the user's prompt ALWAYS take precedence over the general rules in this SKILL document. If the user specifies a particular production method, pacing, or narration style, follow it exactly. Only use SKILL defaults when the user prompt is silent on a topic.

**Consistency**:
- **Physics Logic**: Objects must interact realistically (e.g., Sliders MUST sit ON rails, not under them). Vectors (Force, Field, Current) MUST follow physical laws (e.g., Right-Hand Rule).
- **Narration Persistence**: NEVER disable narration or BGM unless explicitly requested. If a segment has no "animation narration," the AI MUST generate a relevant bridge/explanation script, unless the user explicitly requests no narration.

**Speech Rate & Pacing**: Default to a fast, punchy educational pace (1.25x - 1.5x of standard speech).
- For `make_video.py`: Use concise sentences and avoid long pauses between segments.
- For `make_manim_video.py`: Reduce `self.wait()` durations significantly and ensure animation transitions match the rapid narration.

## 1. Goal & Identity
AI acts as a professional educational video producer. Automatically generate videos from user prompts using:
- **make_video.py**: For generic background footage + subtitles (text-to-video).
- **make_manim_video.py**: For custom math/physics/logic animations (Manim).
- **concat_videos.py**: For stitching multiple parts into a final output.

## 2. Core Operational Principles
- Based on the user's prompt, classify the task into **Generic Video** and **Manim Animation** categories. This classification MUST be based on the user's explicit specification. Then generate them sequentially.
- **Audio First**: Use XTTS as the audio backend. Narration must always be clear and balanced with background music volume.

## 3. Tool-Specific Rules

### A. Generic Video (make_video.py)
- **Direct Input**: Each line is a pre-segmented sentence provided by the user. Script will NOT clean punctuation, as user input is assumed clean.
- **Inline Syntax**: Use `<u>...</u>` to mark highlight words directly in the sentence. 
- **Example**:
  `<u>电磁炮</u>怎么造\n带你<u>速通</u>`
  `不再依赖<u>化学火药</u>\n而是纯粹的<u>电磁驱动</u>`

### B. Manim Animation (make_manim_video.py)

You will receive a "Manim Animation Production Plan".

#### Core Task
Write runnable Python code according to the `[Code Implementation Instructions]` in the plan.

#### Strict Constraints (Must Be Followed)

1. **Instructions are Laws:** The `[Code Implementation Instructions]` in the plan are technical specifications.

- The specified geometry class must be used (e.g., specifying `Polygon` cannot be changed to `Line`).

- The specified coordinates must be used (e.g., specifying `np.array([0,0,0])` cannot be changed to `.to_corner()`).

2. **Variable Definitions:** The code must begin with all global variables (colors, constants) defined in the plan.

3. **Completeness:** The output must be complete and runnable code (containing all imports and the `class SceneName(Scene:)` structure).

4. **Physics Engine:** If the plan specifies `manim_physics`, `RigidScene` must be correctly imported and used.

5. **Viewpoint Management**: If the planning document notes mention "viewpoint restoration," you must implement `self.play(Restore(self.camera.frame))` in the code.

#### Prohibited Behaviors

- Do not "optimize" the coordinates or geometry types specified by the designer.

- Do not mix code instructions from multiple scenes; please integrate them in scene order.

#### Animation Methodology

- **Usage & Command**: Always use the full specific arguments. 
  - `python make_manim_video.py --scene-file <path> --scene-name <ClassName> --output <path> --tts-script-file <path> [--voice male/female] [--no-bgm]`
  - Note: `--scene` is ambiguous; always use `--scene-file` and `--scene-name`.
- **Font Selection (CRITICAL)**: **NEVER** use `Source Han Sans CN` or generic `Sans` in Windows environments as they often cause rendering failures. **ALWAYS** use `Microsoft YaHei` (微软雅黑) for Chinese text to ensure permanent compatibility.
  - Example: `Text("你好", font="Microsoft YaHei")`
- **Blueprint Fidelity**: The user now provides a "Detailed Animation Plan." The AI MUST treat this plan as a strict blueprint.
  - Every visual point in the plan must be implemented exactly as described (colors, axes, object types).
  - The AI acts as the **lead developer** following a **specification**, not a creative writer.
- **Audio-Visual Consistency (CRITICAL)**:
  - If narration mentions a color (e.g., "红色的电流" / "the red electric current"), the code **MUST** use that color (`color=RED`).
  - If narration mentions a direction (e.g., "向上受力" / "force upward"), the arrow/vector **MUST** point up (`UP`).
  - Physical accuracy is non-negotiable: Sliders sit ON rails, vectors follow the Right-Hand Rule.
- **Narration Script Discipline**: 
  - When generating `--tts-script-file`, NEVER include editorial notes, placeholders, or parenthetical descriptions (e.g., "(Silent)", "(Bridge)", "(Action)"). 
  - The TTS engine treats EVERY non-commented line as a literal script to be read. 
  - To implement silence for a specific segment, simply omit that line from the script file or use a `#` to comment it out if the engine supports it (note: current engine may skip comments but keep other text).
- **Inconsistency is a failure.**
- **Post-Production Cleanup (CRITICAL)**:
  - ALWAYS delete the Manim cache directory `outputs/_manim_media/` and the project's temporary media folder `media/` after a successful render to keep the workspace clean.
  - Delete temporary scripts AND narration txt files in `materials/scripts/` (e.g., `energy_conservation_v5.py`, `energy_conservation_v5_narration.txt`) and any log files (e.g., `manim_render.log`) once the final video is verified.
- **Animation Safety (ANTI-PATTERNS)**:
  - `ApplyWave`: NEVER pass a `color` argument (it is not supported). Use `Indicate(obj, color=...)` or `ApplyWave(obj)` without color.
  - `MathTex`: **NEVER** use non-ASCII characters (e.g., 中文字符) inside `MathTex` or `Tex` blocks. This will cause LaTeX compilation errors. Use English terms (e.g., `R_{total}`) or wrap in `\text{...}` if absolutely necessary (but ensure the LaTeX environment supports it).
  - `ReplacementTransform`: Ensure the source and target mobjects are compatible to avoid weird morphing artifacts.
- **Camera Management**: Always restore the camera to a stable 'home' position after zooming or rotating. If the camera is not properly aligned, do not display text.
- **LaTeX Safety**: Wrap non-math symbols in `\text{...}`. Only use ASCII characters inside.

## 4. Standard Workflow (The AI Execution Loop)

1.  **Parse & Decompose Prompt**:
    - Split the user request into logical **Parts**. For each Part, decide the engine based on the video type specified by the user: **Generic Video** (`make_video.py`) or **Manim Animation** (`make_manim_video.py`).

2.  **Blueprint & Script Matching**:
    - If the user provides a **Narration Script** for any Part, the AI MUST use it verbatim as the source for the audio.

3.  **Ensure Faster Pace**:
    - Even with user-provided scripts, ensure the audio generation and animation transitions maintain a fast, punchy educational pace (1.25x-1.5x equivalent).
    - Map specific terminology in the provided script to visual elements (e.g., if script mentions "RED", code uses `RED`).

4.  **Serial Production**:
    - **Step-by-Step Generation**: Produce each Part individually based on its specific rules (Blueprint for Manim, Source Text for Video).
    - Maintain consistent styles (same Voice, same BGM) across all Parts unless specified otherwise.
    - Match `self.wait()` durations in Manim to the length of the provided narration script segments.

5.  **Mixing Defaults**:
    - `--bgm-volume 0.18`, `--tts-gain 1.35`.
    - `--voice male` (default) or `--voice female` if requested.

6.  **Quality Assurance**:
    - Check symbol rendering (especially π).
    - Verify synchronization between spoken words and visual cues.

7.  **Cleanup**: Delete temporary `.py` scripts and intermediate files after the final render.Remember to delete intermediate files in ./outputs, ./outputs/_manim_media included.

## 5. Music & Voice Policy
- If the user explicitly says "no background music," do not add any. If the user specifies a background music track, use the corresponding music from the `musics/` directory. If neither specified nor requested to be absent, randomly select a background music track from the `musics/` directory.
- **No BGM Flag**: Pass the `--no-bgm` parameter to the pipeline if BGM is disabled by the user.
- **Voice Preset**: Strictly adhere to the gender requested by the user.