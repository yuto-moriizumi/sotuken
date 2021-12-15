import math


def hit_sector(center_x, center_y, target_x, target_y, start_angle, end_angle, radius):
    dx = target_x - center_x
    dy = target_y - center_y
    if start_angle > end_angle:
        # print(f"swap,{start_angle} {end_angle}")
        start_angle, end_angle = end_angle, start_angle
        # print(f"swapped,{start_angle} {end_angle}")
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


def course_convert(course: float):
    """NMEAのcouse(進行方向)を、真東0°、真北90°の角度に変換する"""
    return (course*-1+90+360) % 360


start = course_convert(30)
end = course_convert(60)
res = hit_sector(137.7675, 34.7132, 137.7675, 39.7132,
                 start, end, 100)
print(f"start:{end} end:{start} res:{res}")

# print(course_convert(0))  # to be 90
# print(course_convert(90))  # to be 0
# print(course_convert(180))  # to be 270
# print(course_convert(270))  # to be 180
# print(course_convert(-360))  # to be 90
