import cv2
import numpy as np

COLS, ROWS = 9, 6
CELL_PX = 80
W, H = COLS * CELL_PX, ROWS * CELL_PX

ARUCO_DICT = cv2.aruco.DICT_4X4_50
MARKER_IDS = [27, 28, 29]
ROW_LETTERS = ['А', 'Б', 'В', 'Г', 'Д', 'Е']

MARKER_SIZE_MM = 17.0
CELL_MM = 29.0

def detect_aruco(frame):
    d = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    det = cv2.aruco.ArucoDetector(d, cv2.aruco.DetectorParameters())
    corners, ids, _ = det.detectMarkers(frame)
    return corners, ids


def marker_px_per_mm(marker_corner):

    sides = []
    for i in range(4):
        p1 = marker_corner[i]
        p2 = marker_corner[(i + 1) % 4]
        sides.append(np.linalg.norm(p2 - p1))
    mean_side_px = float(np.mean(sides))
    return mean_side_px / MARKER_SIZE_MM


def get_field_corners_px(markers_corners, ids):
    if ids is None:
        return None

    m = {}
    for i, mid in enumerate(ids.flatten()):
        m[int(mid)] = markers_corners[i][0]

    if not all(mid in m for mid in MARKER_IDS):
        return None

    c_ln_base = m[27][0]   
    c_pn_base = m[28][1]    
    c_pv_base = m[29][0]    

    px_per_mm_27 = marker_px_per_mm(m[27])
    px_per_mm_28 = marker_px_per_mm(m[28])
    px_per_mm_29 = marker_px_per_mm(m[29])

    off_ln_mm = (-7.0,  -7.0)    
    off_pn_mm = (+7.0, -7.0)    
    off_pv_mm = (-7.0, -7.0)    
    off_lv_mm = (-5.0,  -4.0)   

    c_ln = c_ln_base + np.float32([
        off_ln_mm[0] * px_per_mm_27,
        off_ln_mm[1] * px_per_mm_27,
    ])
    c_pn = c_pn_base + np.float32([
        off_pn_mm[0] * px_per_mm_28,
        off_pn_mm[1] * px_per_mm_28,
    ])
    c_pv = c_pv_base + np.float32([
        off_pv_mm[0] * px_per_mm_29,
        off_pv_mm[1] * px_per_mm_29,
    ])

    c_lv = c_ln + (c_pv - c_pn)
    px_per_mm_lv = (px_per_mm_27 + px_per_mm_29) / 2.0
    c_lv = c_lv + np.float32([
        off_lv_mm[0] * px_per_mm_lv,
        off_lv_mm[1] * px_per_mm_lv,
    ])


    return np.float32([c_ln, c_pn, c_pv, c_lv])


def build_bird_eye(frame, corners):
    dst = np.float32([
        [0, H],
        [W, H],
        [W, 0],
        [0, 0],
    ])
    M = cv2.getPerspectiveTransform(corners, dst)
    warped = cv2.warpPerspective(frame, M, (W, H))
    return warped, M

COLOR_SAT_THRESHOLD = 80 
COLOR_PIXEL_FRACTION = 0.05  


def is_piece(warped, col, row_top):

    cx = col * CELL_PX + CELL_PX // 2
    cy = row_top * CELL_PX + CELL_PX // 2
    r = int(CELL_PX * 0.35)  
    x1 = max(0, cx - r)
    y1 = max(0, cy - r)
    x2 = min(W, cx + r)
    y2 = min(H, cy + r)

    roi = warped[y1:y2, x1:x2]
    if roi.size == 0:
        return False
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv,
                       (0, COLOR_SAT_THRESHOLD, 40),
                       (179, 255, 255))

    colored_px = cv2.countNonZero(mask)
    total_px = roi.shape[0] * roi.shape[1]

    if total_px == 0:
        return False

    return (colored_px / total_px) >= COLOR_PIXEL_FRACTION

def find_pieces(warped):
    pieces = []
    for row_top in range(ROWS):
        for col in range(COLS):
            if is_piece(warped, col, row_top):
                letter = ROW_LETTERS[ROWS - 1 - row_top]
                pieces.append(f"{letter}{col}")
    return pieces


def draw_grid_on_warped(warped, pieces):
    for r in range(ROWS + 1):
        cv2.line(warped, (0, r * CELL_PX), (W, r * CELL_PX), (0, 200, 0), 1)
    for c in range(COLS + 1):
        cv2.line(warped, (c * CELL_PX, 0), (c * CELL_PX, H), (0, 200, 0), 1)

    for row_top in range(ROWS):
        for col in range(COLS):
            code = f"{ROW_LETTERS[ROWS - 1 - row_top]}{col}"
            occupied = code in pieces
            color = (0, 0, 255) if occupied else (0, 200, 0)
            x1, y1 = col * CELL_PX, row_top * CELL_PX
            if occupied:
                cv2.rectangle(warped, (x1 + 4, y1 + 4),
                              (x1 + CELL_PX - 4, y1 + CELL_PX - 4),
                              color, 2)
            cv2.putText(warped, code, (x1 + 5, y1 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)

    cv2.rectangle(warped, (0, 0), (W - 1, H - 1), (0, 255, 255), 3)


def draw_grid_on_original(frame, field_corners):
    src = np.float32([[0, H], [W, H], [W, 0], [0, 0]])
    dst = field_corners.astype(np.float32)
    M = cv2.getPerspectiveTransform(src, dst)

    for r in range(ROWS + 1):
        pts = np.float32([[[0, r * CELL_PX]], [[W, r * CELL_PX]]])
        pts_t = cv2.perspectiveTransform(pts, M).astype(int)
        cv2.line(frame, tuple(pts_t[0][0]), tuple(pts_t[1][0]), (0, 200, 0), 1)
    for c in range(COLS + 1):
        pts = np.float32([[[c * CELL_PX, 0]], [[c * CELL_PX, H]]])
        pts_t = cv2.perspectiveTransform(pts, M).astype(int)
        cv2.line(frame, tuple(pts_t[0][0]), tuple(pts_t[1][0]), (0, 200, 0), 1)


def draw_field_on_original(frame, field_corners, markers_corners, ids):
    cv2.polylines(frame, [field_corners.astype(np.int32)],
                  True, (0, 255, 255), 3)

    labels = ["ЛН", "ПН", "ПВ", "ЛВ"]
    colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 0, 255)]
    for i, p in enumerate(field_corners.astype(int)):
        cv2.circle(frame, tuple(p), 8, colors[i], -1)
        cv2.circle(frame, tuple(p), 10, (255, 255, 255), 2)
        cv2.putText(frame, labels[i], (p[0] + 12, p[1] - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, colors[i], 2)

    if ids is not None:
        for i, mid in enumerate(ids.flatten()):
            c = markers_corners[i][0].astype(int)
            cv2.polylines(frame, [c], True, (0, 255, 0), 2)
            center = c.mean(axis=0).astype(int)
            cv2.putText(frame, f"id{int(mid)}",
                        (center[0] - 20, center[1] + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)




cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
for _ in range(10):
    cap.read()

while True:
    ret, frame = cap.read()
    if not ret:
        break
    markers_corners, ids = detect_aruco(frame)
    field_corners = get_field_corners_px(markers_corners, ids)

    if field_corners is not None:
        warped, M = build_bird_eye(frame, field_corners)
        pieces = find_pieces(warped)

        vis_warped = warped.copy()
        draw_grid_on_warped(vis_warped, pieces)

        draw_grid_on_original(frame, field_corners)
        draw_field_on_original(frame, field_corners,
                                markers_corners, ids)

        cv2.putText(frame, f"Найдено шашек: {len(pieces)}",
                    (10, 35), cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (0, 255, 255), 2)

        print("Шашки:", pieces)

        cv2.imshow("Win", vis_warped)
    else:
        cv2.putText(frame, "Мало маркеров — нужно 27, 28, 29",
                    (10, 35), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 0, 255), 2)

    cv2.imshow("Original", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()