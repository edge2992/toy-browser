import skia


def parse_color(color):
    if color == "white":
        return skia.ColorWHITE
    elif color == "black":
        return skia.ColorBLACK
    elif color == "lightblue":
        return skia.ColorSetARGB(0xFF, 0xAD, 0xD8, 0xE6)
    elif color == "orange":
        return skia.ColorSetARGB(0xFF, 0xFF, 0xA5, 0x00)
    elif color == "red":
        return skia.ColorRED
    elif color == "green":
        return skia.ColorGREEN
    elif color == "blue":
        return skia.ColorBLUE
    elif color == "gray":
        return skia.ColorGRAY
    elif color == "lightgray":
        return skia.ColorSetARGB(0xFF, 0xD3, 0xD3, 0xD3)
    elif color == "lightgreen":
        return skia.ColorSetARGB(0xFF, 0x90, 0xEE, 0x90)
    elif isinstance(color, str) and color.startswith("#") and len(color) == 7:
        return skia.ColorSetARGB(
            0xFF, int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        )
    elif isinstance(color, str) and color.startswith("#") and len(color) == 4:
        # 3桁のカラーコードを6桁に変換
        return skia.ColorSetARGB(
            0xFF, int(color[1] * 2, 16), int(color[2] * 2, 16), int(color[3] * 2, 16)
        )
    else:
        print("[warining] unknown color", color)
        return skia.ColorBLACK


def draw_line(canvas, x1, y1, x2, y2):
    path = skia.Path().moveTo(x1, y1).lineTo(x2, y2)
    paint = skia.Paint(Color=skia.ColorBLACK)
    paint.setStyle(skia.Paint.kStroke_Style)
    paint.setStrokeWidth(1)
    canvas.drawPath(path, paint)


def draw_text(canvas, x, y, text, font, color=None):
    sk_color = parse_color(color)
    paint = skia.Paint(AntiAlias=True, Color=sk_color)
    canvas.drawString(text, float(x), y - font.getMetrics().fAscent, font, paint)


def draw_rect(canvas, left, top, right, bottom, fill=None, width=1):
    paint = skia.Paint()
    if fill:
        paint.setStrokeWidth(width)
        paint.setColor(parse_color(fill))
    else:
        paint.setStyle(skia.Paint.kStroke_Style)
        paint.setStrokeWidth(width)
        paint.setColor(skia.ColorBLACK)
    rect = skia.Rect.MakeLTRB(left, top, right, bottom)
    canvas.drawRect(rect, paint)


def linespace(font: skia.Font):
    metrics = font.getMetrics()
    return metrics.fDescent - metrics.fAscent
