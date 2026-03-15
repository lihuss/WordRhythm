# WordRhythm - 跨平台自动化知识博主视频制作系统

WordRhythm 是一款专为 **抖音、快手、B站** 等视频平台打造的自动化视频制作系统。它通过 **Manim** 动画引擎与 **动态文字切换视频** 的深度结合，能够快速生成具有高度专业感和视觉冲击力的理科知识讲解视频。

本系统不仅局限于基础物理教学，更可广泛应用于 **数学、物理、化学** 乃至 **电磁学、控制论、量子力学** 等高深细分学科的知识科普。只要能通过“文字视频 + Manim 动画”组合讲解的内容，都在 WordRhythm 的能力覆盖之内。

## 核心理念：混合生产流

WordRhythm 提供两套互补的引擎：
1. **make_text_video.py**：生成极具节奏感的动态文字切换视频，适合作为快节奏的开场、过渡或核心观点强调。
2. **make_manim_video.py**：生成严谨、丝滑的数学/物理公式推导及逻辑动画。
3. **video_cli.py**：通过简单的命令行将上述两种视频无缝拼接，构建完整的短视频闭环。

## 核心特性

- **多学科适配**：内置处理逻辑支持从基础理科到前沿工业软件理论的各种公式与逻辑展示。
- **XTTS-v2 语音合成**：内置高质量中英文配音，自动处理 LaTeX 专业术语的语音归一化。
- **高度自动化**：一键完成从脚本分割、音频对位、动画渲染到视频打包的全流程。
- **视觉风格自定义**：针对短视频平台优化的深色模式背景与高对比度强调色方案。

## 项目结构

```
WordRhythm/
├── materials/              # 素材库
│   ├── fonts/              # 系统字体
│   ├── musics/             # 背景音乐
│   └── voices/             # XTTS 参考语音 (male.wav, female.wav)
├── src/                    # 核心源代码
│   ├── core/               # 核心逻辑 (音频、动画、流水线)
│   │   ├── audio/          # TTS 引擎
│   │   ├── animations/     # Manim 场景定义
│   │   └── utils/          # 文本分割与处理
├── outputs/                # 视频输出目录
├── make_manim_video.py     # Manim 场景视频生成脚本
├── make_text_video.py      # 纯文字/通用背景视频生成脚本
├── video_cli.py           # 视频连接/后处理工具
├── xtts_config.json        # XTTS 配置文件
└── requirements.txt        # 依赖清单
```

## 快速开始

### 1. 环境配置

建议使用 Python 3.10+ 环境。

```bash
pip install -r requirements.txt
```

*注意：Manim 需要系统安装 LaTeX (如 MiKTeX 或 TeX Live) 和 FFmpeg。*

### 2. 准备解说脚本

创建一个 `narration.txt` 文件，写入每一段的解说内容：

```text
这道题我们使用能量守恒定律。
重力做功加上外力做功等于动能增量。
```

### 3. 生成视频

运行以下命令生成带配音的 Manim 视频：

```bash
python make_manim_video.py --scene-file src/core/animations/energy_conservation_scene_v2.py --scene-name EnergyConservationPhysicsV2 --output outputs/result.mp4 --tts-script-file narration.txt --voice male --no-bgm --quality l
```

### 4. 连接视频
如果你有多个分屏视频需要合并，可以使用：
```bash
python video_cli.py input1.mp4 input2.mp4 output.mp4
```

#### 关键参数说明：
- `--scene-file`: 指定 Manim 源代码文件。
- `--scene-name`: 指定要渲染的类名。
- `--tts-script-file`: 提供解说词脚本。
- `--voice`: `male` (男声) 或 `female` (女声)。
- `--quality`: 渲染质量 (`l`: 480p, `m`: 720p, `h`: 1080p, `p`: 1440p, `k`: 4k)。

## 📘 物理场景开发指南

在编写新的 Manim 场景时，请遵循以下规则：
1. **公式下标**：避免在 `MathTex` 中使用中文下标（如 `R_总`），请替换为英文（如 `R_{total}`）以确保跨平台编译兼容性。
2. 待续...

---

*Powered by Manim Community & Coqui TTS.*
