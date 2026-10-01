import random
import pygame

from game.block import Block


class Debris:
    """A trimmed piece of a block that falls away with gravity."""

    def __init__(self, x, y, width, height, color, velocity_x=0):
        self.x = float(x)
        self.y = float(y)
        self.width = max(2.0, float(width))
        self.height = max(2.0, float(height))
        self.color = color

        self.velocity_x = float(velocity_x)
        self.velocity_y = -1.5

        self.gravity = 0.35
        self.angle = 0.0
        self.angular_velocity = random.uniform(-7.0, 7.0)

    def update(self):
        # Gravity increases downward velocity.
        self.velocity_y += self.gravity

        # Move debris.
        self.x += self.velocity_x
        self.y += self.velocity_y

        # Rotate debris.
        self.angle += self.angular_velocity

    def is_off_screen(self, screen_height):
        return self.y > screen_height + 100

    def render(self, surface):
        # Create transparent surface for the debris.
        debris_surface = pygame.Surface(
            (
                max(2, int(self.width)),
                max(2, int(self.height)),
            ),
            pygame.SRCALPHA,
        )

        # Draw debris.
        pygame.draw.rect(
            debris_surface,
            self.color,
            debris_surface.get_rect(),
        )

        # Draw border.
        pygame.draw.rect(
            debris_surface,
            (245, 245, 250),
            debris_surface.get_rect(),
            width=2,
        )

        # Rotate debris.
        rotated = pygame.transform.rotate(
            debris_surface,
            self.angle,
        )

        # Keep rotation centered.
        draw_x = int(
            self.x
            + self.width / 2
            - rotated.get_width() / 2
        )

        draw_y = int(
            self.y
            + self.height / 2
            - rotated.get_height() / 2
        )

        surface.blit(
            rotated,
            (draw_x, draw_y),
        )


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.block_height = 28
        self.base_width = 180

        # Fonts.
        self.font_title = pygame.font.SysFont(
            None,
            38,
        )

        self.font_hud = pygame.font.SysFont(
            None,
            28,
        )

        self.font_big = pygame.font.SysFont(
            None,
            46,
        )

        self.font_perfect = pygame.font.SysFont(
            None,
            40,
        )

        self.reset()

    def get_color(self, index):
        palette = [
            (230, 75, 75),    # Crimson
            (240, 140, 45),   # Orange
            (245, 210, 50),   # Gold
            (60, 195, 110),   # Green
            (50, 150, 240),   # Blue
            (165, 80, 225),   # Purple
        ]

        return palette[index % len(palette)]

    def reset(self):
        self.score = 0
        self.bonus_score = 0
        self.perfect_streak = 0
        self.game_over = False

        # PERFECT popup.
        self.perfect_popup_timer = 0
        self.perfect_popup_duration = 70

        # TASK 3:
        # Store all falling debris pieces.
        self.debris = []

        # Base block.
        base_x = (self.width - self.base_width) / 2
        base_y = self.height - 60

        base_block = Block(
            base_x,
            base_y,
            self.base_width,
            self.block_height,
            self.get_color(0),
            speed=0,
        )

        self.stack = [base_block]

        self.spawn_active_block()

    def spawn_active_block(self):
        top_block = self.stack[-1]

        # Position above current tower.
        next_y = (
            top_block.y
            - self.block_height
            - 4
        )

        # Increase speed as tower grows.
        speed = min(
            10.0,
            4.5 + (len(self.stack) * 0.35),
        )

        color = self.get_color(
            len(self.stack)
        )

        # Start from either side.
        if random.choice([True, False]):
            start_x = 25
        else:
            start_x = (
                self.width
                - 25
                - top_block.width
            )

        self.active_block = Block(
            start_x,
            next_y,
            top_block.width,
            self.block_height,
            color,
            speed=speed,
        )

    def create_debris(self, act, top_block):
        """
        Create debris from the part of the active block
        that hangs outside the previous block.
        """

        # ---------------------------------------------
        # LEFT OVERHANG
        # ---------------------------------------------

        if act.x < top_block.x:
            overhang_width = min(
                act.width,
                top_block.x - act.x,
            )

            if overhang_width > 0:
                debris = Debris(
                    x=act.x,
                    y=act.y,
                    width=overhang_width,
                    height=self.block_height,
                    color=act.color,
                    velocity_x=-1.5,
                )

                self.debris.append(debris)

        # ---------------------------------------------
        # RIGHT OVERHANG
        # ---------------------------------------------

        active_right = (
            act.x + act.width
        )

        top_right = (
            top_block.x
            + top_block.width
        )

        if active_right > top_right:
            overhang_width = min(
                act.width,
                active_right - top_right,
            )

            if overhang_width > 0:
                debris = Debris(
                    x=top_right,
                    y=act.y,
                    width=overhang_width,
                    height=self.block_height,
                    color=act.color,
                    velocity_x=1.5,
                )

                self.debris.append(debris)

    def drop_block(self):
        if self.game_over:
            return

        top_block = self.stack[-1]
        act = self.active_block

        # ---------------------------------------------
        # CALCULATE HORIZONTAL OVERLAP
        # ---------------------------------------------

        left = max(
            act.x,
            top_block.x,
        )

        right = min(
            act.x + act.width,
            top_block.x + top_block.width,
        )

        overlap = right - left

        # ---------------------------------------------
        # TASK 1
        #
        # Positive overlap = successful placement.
        # No overlap = game over.
        # ---------------------------------------------

        is_successful_drop = overlap > 0

        if not is_successful_drop:
            self.game_over = True
            return

        # ---------------------------------------------
        # TASK 2
        # PERFECT PLACEMENT
        # ---------------------------------------------

        alignment_error = abs(
            act.x - top_block.x
        )

        # 10 pixels makes the PERFECT easier
        # to demonstrate during the lab.
        is_perfect = alignment_error <= 10

        if is_perfect:

            # Keep the complete width.
            # Snap directly into alignment.
            new_block = Block(
                top_block.x,
                act.y,
                top_block.width,
                self.block_height,
                act.color,
                speed=0,
            )

            self.stack.append(
                new_block
            )

            # Normal height score.
            self.score += 1

            # PERFECT bonus.
            self.bonus_score += 2

            # Increase streak.
            self.perfect_streak += 1

            # Show PERFECT popup.
            self.perfect_popup_timer = (
                self.perfect_popup_duration
            )

            # -----------------------------------------
            # THREE PERFECTS IN A ROW
            # -----------------------------------------

            if self.perfect_streak >= 3:

                expansion = 8

                expanded_width = min(
                    self.base_width,
                    new_block.width
                    + expansion,
                )

                # Keep block centered.
                center_x = (
                    new_block.x
                    + new_block.width / 2
                )

                new_block.width = (
                    expanded_width
                )

                new_block.x = (
                    center_x
                    - expanded_width / 2
                )

                # Extra combo bonus.
                self.bonus_score += 3

                # Reset streak after combo.
                self.perfect_streak = 0

        else:

            # -----------------------------------------
            # TASK 3
            #
            # Turn the hanging portion into debris.
            # -----------------------------------------

            self.create_debris(
                act,
                top_block,
            )

            # Keep only the overlapping part.
            trimmed_width = max(
                10.0,
                overlap,
            )

            new_block = Block(
                left,
                act.y,
                trimmed_width,
                self.block_height,
                act.color,
                speed=0,
            )

            self.stack.append(
                new_block
            )

            self.score += 1

            # Non-perfect placement breaks streak.
            self.perfect_streak = 0

        # ---------------------------------------------
        # CAMERA / TOWER SCROLLING
        # ---------------------------------------------

        if new_block.y < 180:

            shift_amount = (
                self.block_height + 4
            )

            for block in self.stack:
                block.y += shift_amount

        # Spawn next block.
        self.spawn_active_block()

    def handle_event(self, event):

        # ---------------------------------------------
        # GAME OVER CONTROLS
        # ---------------------------------------------

        if self.game_over:

            if (
                event.type == pygame.KEYDOWN
                and event.key in (
                    pygame.K_r,
                    pygame.K_SPACE,
                )
            ) or (
                event.type
                == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            ):
                self.reset()

            return

        # ---------------------------------------------
        # SPACE TO DROP
        # ---------------------------------------------

        if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_SPACE
        ):
            self.drop_block()

        # ---------------------------------------------
        # LEFT CLICK TO DROP
        # ---------------------------------------------

        elif (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            self.drop_block()

    def update(self):

        # Move active block.
        if not self.game_over:
            self.active_block.update(
                self.width
            )

        # ---------------------------------------------
        # TASK 3
        # UPDATE FALLING DEBRIS
        # ---------------------------------------------

        for debris in self.debris:
            debris.update()

        # Remove debris once it is far below screen.
        self.debris = [
            debris
            for debris in self.debris
            if not debris.is_off_screen(
                self.height
            )
        ]

        # ---------------------------------------------
        # PERFECT POPUP TIMER
        # ---------------------------------------------

        if self.perfect_popup_timer > 0:
            self.perfect_popup_timer -= 1

    def render(self, screen):

        # ---------------------------------------------
        # BACKGROUND
        # ---------------------------------------------

        screen.fill(
            (24, 27, 36)
        )

        # ---------------------------------------------
        # TITLE
        # ---------------------------------------------

        title_surf = self.font_title.render(
            "Skyscraper Stack",
            True,
            (245, 245, 245),
        )

        screen.blit(
            title_surf,
            (
                self.width // 2
                - title_surf.get_width() // 2,
                16,
            ),
        )

        # ---------------------------------------------
        # HEIGHT
        # ---------------------------------------------

        score_surf = self.font_hud.render(
            f"Height: {self.score}",
            True,
            (255, 220, 80),
        )

        screen.blit(
            score_surf,
            (
                self.width // 2
                - score_surf.get_width() // 2,
                54,
            ),
        )

        # ---------------------------------------------
        # BONUS
        # ---------------------------------------------

        bonus_surf = self.font_hud.render(
            f"Bonus: +{self.bonus_score}",
            True,
            (255, 210, 70),
        )

        screen.blit(
            bonus_surf,
            (15, 15),
        )

        # ---------------------------------------------
        # PERFECT STREAK
        # ---------------------------------------------

        if self.perfect_streak > 0:

            streak_surf = self.font_hud.render(
                f"Perfect Streak: {self.perfect_streak}",
                True,
                (255, 215, 80),
            )

            screen.blit(
                streak_surf,
                (15, 45),
            )

        # ---------------------------------------------
        # RENDER TOWER
        # ---------------------------------------------

        for block in self.stack:
            block.render(screen)

        # ---------------------------------------------
        # TASK 3
        # RENDER FALLING DEBRIS
        # ---------------------------------------------

        for debris in self.debris:
            debris.render(screen)

        # ---------------------------------------------
        # ACTIVE BLOCK
        # ---------------------------------------------

        if not self.game_over:
            self.active_block.render(
                screen
            )

        # ---------------------------------------------
        # PERFECT POPUP
        # ---------------------------------------------

        if self.perfect_popup_timer > 0:

            perfect_surf = (
                self.font_perfect.render(
                    "PERFECT!",
                    True,
                    (255, 215, 0),
                )
            )

            popup_progress = (
                self.perfect_popup_duration
                - self.perfect_popup_timer
            )

            popup_y = (
                105
                - popup_progress * 0.5
            )

            screen.blit(
                perfect_surf,
                (
                    self.width // 2
                    - perfect_surf.get_width() // 2,
                    int(popup_y),
                ),
            )

        # ---------------------------------------------
        # GAME OVER SCREEN
        # ---------------------------------------------

        if self.game_over:

            overlay = pygame.Surface(
                (self.width, self.height),
                pygame.SRCALPHA,
            )

            overlay.fill(
                (0, 0, 0, 195)
            )

            screen.blit(
                overlay,
                (0, 0),
            )

            # Game over title.
            over_surf = self.font_big.render(
                "TOWER COLLAPSED!",
                True,
                (240, 75, 75),
            )

            screen.blit(
                over_surf,
                (
                    self.width // 2
                    - over_surf.get_width() // 2,
                    self.height // 2 - 70,
                ),
            )

            # Final height.
            final_surf = self.font_hud.render(
                f"Final Height: {self.score}",
                True,
                (255, 255, 255),
            )

            screen.blit(
                final_surf,
                (
                    self.width // 2
                    - final_surf.get_width() // 2,
                    self.height // 2 - 20,
                ),
            )

            # Bonus score.
            bonus_final_surf = (
                self.font_hud.render(
                    f"Perfect Bonus: +{self.bonus_score}",
                    True,
                    (255, 215, 80),
                )
            )

            screen.blit(
                bonus_final_surf,
                (
                    self.width // 2
                    - bonus_final_surf.get_width() // 2,
                    self.height // 2 + 20,
                ),
            )

            # Restart message.
            restart_surf = self.font_hud.render(
                "Press [Space] or [R] to Play Again",
                True,
                (200, 200, 200),
            )

            screen.blit(
                restart_surf,
                (
                    self.width // 2
                    - restart_surf.get_width() // 2,
                    self.height // 2 + 65,
                ),
            )