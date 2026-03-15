from manim import *
import numpy as np

class EnergyConservationPhysicsV2(Scene):
    def construct(self):
        # 1. Setup Layout & Main Equation
        color_input = RED_C
        color_output = YELLOW_C
        color_teal = TEAL
        
        main_eq = MathTex(
            "W_F", "+", "W_G", "=", "\\Delta E_k", "+", "Q",
            tex_to_color_map={
                "W_F": color_input, 
                "W_G": color_input, 
                "\\Delta E_k": color_output, 
                "Q": color_output
            }
        ).scale(1.2).to_edge(UP, buff=0.5)

        # --- Scene 01: System Overview ---
        system_group = self.draw_system(color_teal)
        self.play(Create(system_group))
        
        # Energy pointers
        wf_arrow = Arrow(start=RIGHT*3+UP*2, end=np.array([1.5, -0.5, 0]), color=color_input)
        wf_text = Text("外力做功 WF", font="Microsoft YaHei", font_size=20, color=color_input).next_to(wf_arrow, UP)
        
        wg_arrow = Arrow(start=LEFT*4+UP*3, end=np.array([-2.5, 0.5, 0]), color=color_input)
        wg_text = Text("重力做功 WG", font="Microsoft YaHei", font_size=20, color=color_input).next_to(wg_arrow, UP)
        
        self.play(GrowArrow(wf_arrow), Write(wf_text), GrowArrow(wg_arrow), Write(wg_text))
        self.play(Write(main_eq))
        self.wait(1)
        
        # Setup Layout
        self.play(
            system_group.animate.scale(0.5).move_to(np.array([-4.5, -2, 0])),
            FadeOut(wf_arrow), FadeOut(wf_text), FadeOut(wg_arrow), FadeOut(wg_text),
            main_eq.animate.scale(0.8).to_edge(UP, buff=0.3)
        )
        self.wait(1)

        # --- Scene 02: Kinematics & WG ---
        calc_area_x = 2
        title1 = Text("① 位移与重力做功", font="Microsoft YaHei", font_size=24).move_to(np.array([calc_area_x, 2.5, 0]))
        knowns1 = MathTex("t=1\\text{s}, v_1=1\\text{m/s}, v_2=2\\text{m/s}").scale(0.7).next_to(title1, DOWN)
        
        x_calc = MathTex("x = \\frac{v_1 + v_2}{2} \\cdot t = 1.5\\text{ m}").scale(0.8).next_to(knowns1, DOWN, buff=0.5)
        wg_calc = MathTex("W_G = mg \\cdot x \\cdot \\sin 37^\\circ = 1.8\\text{ J}").scale(0.8).next_to(x_calc, DOWN, buff=0.5)
        wg_calc.set_color_by_tex("1.8", color_input)

        self.play(Write(title1), FadeIn(knowns1))
        self.play(Write(x_calc))
        # Move MN bar in micro-view
        mn_bar = system_group[2]
        self.play(mn_bar.animate.shift(DOWN*0.3 + RIGHT*0.4)) 
        
        self.play(Write(wg_calc))
        
        # Archive WG
        wg_val = MathTex("1.8\\text{ J}", color=color_input).scale(0.7).next_to(main_eq[2], DOWN, buff=0.2)
        self.play(ReplacementTransform(wg_calc[-1].copy(), wg_val))
        self.wait(1)

        # --- Scene 03: Delta Ek & Q ---
        scene3_group = VGroup(title1, knowns1, x_calc, wg_calc)
        self.play(FadeOut(scene3_group))
        
        title2 = Text("② 动能与焦耳热", font="Microsoft YaHei", font_size=24).move_to(np.array([calc_area_x, 2.5, 0]))
        ek_calc = MathTex("\\Delta E_k = \\frac{1}{2}mv_2^2 - \\frac{1}{2}mv_1^2 = 0.3\\text{ J}").scale(0.8).next_to(title2, DOWN, buff=0.5)
        ek_calc.set_color_by_tex("0.3", color_output)
        
        r_calc = MathTex("R_{total} = R_{MN} + R_{OA} = 2\\ \\Omega").scale(0.8).next_to(ek_calc, DOWN, buff=0.5)
        q_calc = MathTex("Q = I^2 \\cdot R_{total} \\cdot t = 8\\text{ J}").scale(0.8).next_to(r_calc, DOWN, buff=0.5)
        q_calc.set_color_by_tex("8", color_output)

        self.play(Write(title2))
        self.play(Write(ek_calc))
        ek_val = MathTex("0.3\\text{ J}", color=color_output).scale(0.7).next_to(main_eq[4], DOWN, buff=0.2)
        self.play(ReplacementTransform(ek_calc[-1].copy(), ek_val))
        
        self.play(Write(r_calc))
        self.play(Write(q_calc))
        q_val = MathTex("8\\text{ J}", color=color_output).scale(0.7).next_to(main_eq[6], DOWN, buff=0.2)
        self.play(ReplacementTransform(q_calc[-1].copy(), q_val))
        self.wait(1)

        # --- Scene 04: Final Assembly ---
        self.play(FadeOut(title2), FadeOut(ek_calc), FadeOut(r_calc), FadeOut(q_calc), FadeOut(system_group))
        
        final_group = VGroup(main_eq, wg_val, ek_val, q_val)
        self.play(final_group.animate.move_to(UP*1.5).scale(1.5))
        
        #WF + 1.8 = 0.3 + 8
        step1 = MathTex("W_F", "+", "1.8", "=", "0.3", "+", "8").scale(1.5).move_to(ORIGIN)
        step1[0].set_color(WHITE)
        step1[2].set_color(color_input)
        step1[4].set_color(color_output)
        step1[6].set_color(color_output)
        
        self.play(
            ReplacementTransform(main_eq[0].copy(), step1[0]),
            ReplacementTransform(main_eq[1].copy(), step1[1]),
            ReplacementTransform(wg_val, step1[2]),
            ReplacementTransform(main_eq[3].copy(), step1[3]),
            ReplacementTransform(ek_val, step1[4]),
            ReplacementTransform(main_eq[5].copy(), step1[5]),
            ReplacementTransform(q_val, step1[6]),
            FadeOut(main_eq)
        )
        self.wait(1)
        
        step2 = MathTex("W_F", "=", "8.3", "-", "1.8").scale(1.5).move_to(ORIGIN)
        self.play(TransformMatchingTex(step1, step2))
        self.wait(1)
        
        ans = MathTex("W_F = 6.5\\text{ J}").scale(2).move_to(DOWN*1.5).set_color(color_output)
        box = SurroundingRectangle(ans, color=YELLOW, buff=0.3)
        
        self.play(Write(ans))
        self.play(Create(box))
        self.play(Flash(box, color=YELLOW, flash_radius=1.5))
        self.wait(3)

    def draw_system(self, color_teal):
        # Rails
        rail1 = Line(np.array([-4, 1, 0]), np.array([-1, -2, 0]), color=LIGHT_GREY)
        rail2 = Line(np.array([-3, 2, 0]), np.array([0, -1, 0]), color=LIGHT_GREY)
        
        # Circle OA system
        center = np.array([1.5, -1, 0])
        ring = Circle(radius=1.5, color=LIGHT_GREY).move_to(center)
        oa_bar = Line(center, center + np.array([0, 1.5, 0]), color=color_teal, stroke_width=8)
        
        # MN bar
        mn_bar = Line(np.array([-3.8, 1.2, 0]), np.array([-3.2, 1.8, 0]), color=color_teal, stroke_width=8)
        
        return VGroup(rail1, rail2, mn_bar, ring, oa_bar)
