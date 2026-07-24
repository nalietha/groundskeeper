import importlib.util
import os
import unittest
from unittest import mock

# Force headless SDL so pygame can create a display in CI / no-monitor runs.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


def _load_game_class():
    """Loads the game module by file path, exactly like GameService does."""
    path = os.path.join("games", "espresso_express", "game.py")
    spec = importlib.util.spec_from_file_location("espresso_express_game", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.EspressoExpress


try:
    import pygame
    EspressoExpress = _load_game_class()
    _noop = {"set_score_visibility": lambda *_: None, "update_score": lambda *_: None}
    _probe = EspressoExpress(240, 320, {"colors": {}}, _noop)
    pygame.quit()
    PYGAME_OK = True
except Exception:
    PYGAME_OK = False


@unittest.skipUnless(PYGAME_OK, "pygame display not available")
class EspressoExpressFrameworkTests(unittest.TestCase):
    def setUp(self):
        self.callbacks = {"set_score_visibility": mock.Mock(), "update_score": mock.Mock()}

    def tearDown(self):
        pygame.quit()

    def _game(self, width=240, height=320, assets=None):
        return EspressoExpress(width, height, assets or {"colors": {}}, self.callbacks)

    # --- Asset fallbacks ---------------------------------------------------
    def test_constructs_without_any_art(self):
        game = self._game(assets={})
        self.assertIsNotNone(game.player.image)  # drawn fallback, not a crash

    def test_uses_real_image_when_present(self):
        bean = pygame.Surface((32, 40))
        game = self._game(assets={"colors": {}, "player_bean": bean})
        self.assertIs(game.player.image, bean)

    def test_player_fallback_color_is_themeable(self):
        game = self._game(assets={"colors": {"player": [1, 2, 3]}})
        self.assertEqual(tuple(game.player.image.get_at((0, 0))[:3]), (1, 2, 3))

    # --- Screen-agnostic geometry ------------------------------------------
    def test_lane_geometry_for_default_width(self):
        game = self._game(width=240)
        self.assertEqual(game.lanes, [40, 120, 200])
        self.assertEqual(game.lane_lines, [80, 160])

    def test_lane_geometry_scales_to_other_widths(self):
        game = self._game(width=480)
        self.assertEqual(game.lanes, [80, 240, 400])
        self.assertEqual(game.lane_lines, [160, 320])

    def test_player_sits_near_bottom(self):
        game = self._game(height=320)
        self.assertEqual(game.player_y, 270)

    # --- Player movement ---------------------------------------------------
    def test_player_starts_in_middle_lane(self):
        self.assertEqual(self._game().player.current_lane, 1)

    def test_move_clamps_within_lanes(self):
        game = self._game()
        game.player.move(-1)
        game.player.move(-1)
        self.assertEqual(game.player.current_lane, 0)
        for _ in range(5):
            game.player.move(1)
        self.assertEqual(game.player.current_lane, 2)

    def test_move_updates_rect_position(self):
        game = self._game()
        game.player.move(1)
        self.assertEqual(game.player.rect.centerx, game.lanes[2])

    # --- Spawning / despawning ---------------------------------------------
    def test_spawn_adds_sprite(self):
        game = self._game()
        before = len(game.all_sprites)
        game.spawn_entity()
        self.assertEqual(len(game.all_sprites), before + 1)

    def test_falling_object_despawns_past_bottom(self):
        game = self._game(height=320)
        game.spawn_entity()
        falling = next(s for s in game.all_sprites if s is not game.player)
        falling.rect.top = game.height + 5
        game.all_sprites.update()
        self.assertNotIn(falling, game.all_sprites)

    # --- Per-run reset (Play Again correctness) ----------------------------
    def test_reset_run_clears_state(self):
        game = self._game()
        game.score = 250
        game.game_speed = 12.0
        game.spawn_entity()
        game.spawn_entity()
        game.player.move(1)  # off the middle lane

        game._reset_run()

        self.assertEqual(game.score, 0)
        self.assertEqual(game.game_speed, 5.0)
        self.assertEqual(len(game.obstacles), 0)
        self.assertEqual(len(game.collectibles), 0)
        self.assertEqual(game.player.current_lane, 1)  # back to middle
        self.assertEqual(game.player.rect.centerx, game.lanes[1])

    # --- HUD / screens (smoke: must render without error) ------------------
    def test_draw_hud_runs(self):
        game = self._game()
        game.score = 42
        game.draw_hud(best=99)  # should not raise

    def test_message_accepts_custom_font(self):
        game = self._game()
        game.message("Hi", y_offset=10, font=game.hud_font)  # should not raise

    def test_draw_game_over_runs_with_and_without_new_best(self):
        game = self._game()
        game.score = 100
        game._draw_game_over(high_score_so_far=50)   # new best branch
        game._draw_game_over(high_score_so_far=500)  # not a new best

    # --- Score display stepping --------------------------------------------
    def test_score_display_steps_by_50(self):
        game = self._game()
        self.assertEqual(game._stepped_score(0), 0)
        self.assertEqual(game._stepped_score(49), 0)
        self.assertEqual(game._stepped_score(50), 50)
        self.assertEqual(game._stepped_score(137), 100)
        self.assertEqual(game._stepped_score(4999), 4950)

    # --- Stage progression -------------------------------------------------
    def test_stage_boundaries(self):
        game = self._game()
        # (score, expected stage): 500/1000/1500, then every 2000.
        cases = [
            (0, 1), (499, 1),
            (500, 2), (999, 2),
            (1000, 3), (1499, 3),
            (1500, 4), (3499, 4),
            (3500, 5), (5499, 5),
            (5500, 6),
        ]
        for score, expected in cases:
            self.assertEqual(game._stage_for_score(score), expected, f"score={score}")

    def test_stage_advances_at_first_boundary(self):
        game = self._game()
        game.score = 499
        self.assertFalse(game._update_stage(1000))
        self.assertEqual(game.stage, 1)
        game.score = 500
        self.assertTrue(game._update_stage(1000))
        self.assertEqual(game.stage, 2)

    def test_stage_advance_arms_flash(self):
        game = self._game()
        game.score = 500
        game._update_stage(now=1000)
        self.assertEqual(game.stage_flash_until, 1000 + game.STAGE_FLASH_MS)

    def test_stage_advance_increases_speed_per_stage_gained(self):
        game = self._game()
        base_speed = game.game_speed
        game.score = 500  # jump of one stage
        game._update_stage(1000)
        self.assertEqual(game.game_speed, base_speed + game.STAGE_SPEED_BONUS)

    def test_multi_stage_jump_scales_speed(self):
        game = self._game()
        base_speed = game.game_speed
        game.score = 1500  # stage 1 -> 4 in one update (three stages gained)
        game._update_stage(1000)
        self.assertEqual(game.stage, 4)
        self.assertEqual(game.game_speed, base_speed + 3 * game.STAGE_SPEED_BONUS)

    def test_reset_run_resets_stage_and_speed(self):
        game = self._game()
        game.score = 3500
        game._update_stage(1000)
        self.assertEqual(game.stage, 5)
        game._reset_run()
        self.assertEqual(game.stage, 1)
        self.assertEqual(game.stage_flash_until, 0)
        self.assertEqual(game.game_speed, 5.0)

    def test_draw_stage_flash_runs(self):
        game = self._game()
        game.stage = 3
        game._draw_stage_flash()  # should not raise

    # --- Sugar reward / popups ---------------------------------------------
    def test_sugar_points_constant_is_positive(self):
        self.assertGreater(self._game().SUGAR_POINTS, 0)

    def test_add_score_popup_registers(self):
        game = self._game()
        game._add_score_popup(50, 100, game.SUGAR_POINTS, now=1000)
        self.assertEqual(len(game.popups), 1)
        self.assertEqual(game.popups[0]['amount'], game.SUGAR_POINTS)

    def test_popups_expire_after_duration(self):
        game = self._game()
        game._add_score_popup(50, 100, 50, now=0)
        game._draw_popups(now=100)             # still alive
        self.assertEqual(len(game.popups), 1)
        game._draw_popups(now=game.POPUP_MS + 1)  # expired
        self.assertEqual(len(game.popups), 0)

    def test_reset_run_clears_popups(self):
        game = self._game()
        game._add_score_popup(10, 10, 50, now=0)
        game._reset_run()
        self.assertEqual(game.popups, [])

    # --- Intro screen input ------------------------------------------------
    def test_intro_starts_on_a(self):
        game = self._game()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
        self.assertTrue(game._run_intro())

    def test_intro_quits_on_b(self):
        game = self._game()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_b))
        self.assertFalse(game._run_intro())

    def test_intro_quits_on_window_close(self):
        game = self._game()
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.assertFalse(game._run_intro())


if __name__ == "__main__":
    unittest.main()
