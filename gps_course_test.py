import math


def course_convert(course: float):
    """NMEAのcouse(進行方向)を、真東0°、真北90°の角度に変換する"""
    return (course*-1+90+360) % 360


def hit_sector(target_x: float, target_y: float, start_angle: float, end_angle: float, radius: float):
    """真東を0°、真北を90°とする"""
    if start_angle > end_angle:
        start_angle, end_angle = end_angle, start_angle
    dx = target_x
    dy = target_y
    sx = math.cos(math.radians(start_angle))
    sy = math.sin(math.radians(start_angle))
    ex = math.cos(math.radians(end_angle))
    ey = math.sin(math.radians(end_angle))

    # 円の内外判定
    if dx ** 2 + dy ** 2 > radius ** 2:
        return False

    # 扇型の角度が180を超えているか
    if sx * ey - ex * sy > 0:
        # 開始角に対して左にあるか
        if sx * dy - dx * sy < 0:
            return False
        # 終了角に対して右にあるか
        if ex * dy - dx * ey > 0:
            return False
        # 扇型の内部にあることがわかった
        return True
    else:
        # 開始角に対して左にあるか
        if sx * dy - dx * sy >= 0:
            return True
        # 終了角に対して右にあるか
        if ex * dy - dx * ey <= 0:
            return True
        # 扇型の外部にあることがわかった
        return False


COORINATES = [{
    "my_lat": 34.8145,
    "my_lon": 138.0539,
    "my_cource": 0,
    "target_lat": 34.9145,
    "target_lon": 138.0539,
    "expect": True,
}, {
    "my_lat": 34.8145,
    "my_lon": 138.0539,
    "my_cource": 0,
    "target_lat": 34.8145,
    "target_lon": 139.0539,
    "expect": False,
}]

# 方向判定
HIT_ANGLE = 45  # 中心から±何度までの誤差を許容するか
HIT_RADIUS = 100

for d in COORINATES:
    target_lat = d["target_lat"]-d["my_lat"]
    target_lon = d["target_lon"]-d["my_lon"]
    my_corce = d["my_cource"]
    is_hit = hit_sector(
        target_lon, target_lat, course_convert(my_corce-HIT_ANGLE), course_convert(my_corce+HIT_ANGLE), HIT_RADIUS)
    print(is_hit, "expect", d["expect"])
