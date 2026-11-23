import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from scripts.black_friday_motion import smooth_path, analyze_reference


class MotionPipelineTests(unittest.TestCase):
    def test_smooth_path_clamps_bad_tracking(self):
        rows = [
            {"global_transform": [[9.0, 0.0, 9999.0], [0.0, 9.0, -9999.0], [0, 0, 1]]}
            for _ in range(7)
        ]
        out = smooth_path(rows)
        self.assertEqual(out.shape, (7, 4))
        self.assertTrue(np.all(out[:, 0] <= 1.850001))
        self.assertTrue(np.all(out[:, 0] >= 0.619999))
        self.assertTrue(np.all(np.abs(out[:, 2]) <= 220))
        self.assertTrue(np.all(np.abs(out[:, 3]) <= 260))

    def test_analyzer_extracts_all_synthetic_frames(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "synthetic.mp4"
            writer = cv2.VideoWriter(str(src), cv2.VideoWriter_fourcc(*"mp4v"), 10, (160, 200))
            for i in range(8):
                frame = np.zeros((200, 160, 3), np.uint8)
                cv2.rectangle(frame, (10 + i * 3, 30), (80 + i * 3, 120), (255, 255, 255), -1)
                writer.write(frame)
            writer.release()
            out = analyze_reference(src, root / "frames")
            self.assertEqual(out["frame_count"], 8)
            self.assertEqual(len(out["frames"]), 8)
            self.assertEqual(len(list((root / "frames").glob("ref_*.jpg"))), 8)


if __name__ == "__main__":
    unittest.main()
