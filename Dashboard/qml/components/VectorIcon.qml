import QtQuick
import "../themes"

Canvas {
    id: root
    property string name: "dashboard"
    property color iconColor: Theme.textSecondary
    property real strokeWidth: 1.8

    implicitWidth: 18
    implicitHeight: 18

    onNameChanged: requestPaint()
    onIconColorChanged: requestPaint()

    function strokeRoundRect(ctx, x, y, w, h, r) {
        ctx.beginPath()
        ctx.moveTo(x + r, y)
        ctx.lineTo(x + w - r, y)
        ctx.arcTo(x + w, y, x + w, y + r, r)
        ctx.lineTo(x + w, y + h - r)
        ctx.arcTo(x + w, y + h, x + w - r, y + h, r)
        ctx.lineTo(x + r, y + h)
        ctx.arcTo(x, y + h, x, y + h - r, r)
        ctx.lineTo(x, y + r)
        ctx.arcTo(x, y, x + r, y, r)
        ctx.closePath()
        ctx.stroke()
    }

    onPaint: {
        var ctx = getContext("2d")
        ctx.clearRect(0, 0, width, height)
        ctx.strokeStyle = root.iconColor
        ctx.fillStyle = root.iconColor
        ctx.lineWidth = root.strokeWidth
        ctx.lineCap = "round"
        ctx.lineJoin = "round"

        var w = width; var h = height

        if (name === "dashboard") {
            // Bar chart icon (Matching Image #2 sidebar icon 2)
            ctx.beginPath()
            ctx.moveTo(4, 16); ctx.lineTo(4, 6)
            ctx.moveTo(9, 16); ctx.lineTo(9, 3)
            ctx.moveTo(14, 16); ctx.lineTo(14, 10)
            ctx.stroke()
        }
        else if (name === "enrollment") {
            // User outline icon (Matching Image #2 sidebar icon 3)
            ctx.beginPath()
            ctx.arc(w / 2, 6, 3.5, 0, 2 * Math.PI)
            ctx.stroke()
            ctx.beginPath()
            ctx.arc(w / 2, 17, 6.5, Math.PI + 0.3, 2 * Math.PI - 0.3)
            ctx.stroke()
        }
        else if (name === "camera") {
            // Mail envelope icon (Matching Image #2 sidebar icon 4)
            strokeRoundRect(ctx, 2, 4, 14, 10, 2)
            ctx.beginPath()
            ctx.moveTo(2, 4); ctx.lineTo(9, 9); ctx.lineTo(16, 4)
            ctx.stroke()
        }
        else if (name === "settings") {
            // Chat bubble icon (Matching Image #2 sidebar icon 5)
            strokeRoundRect(ctx, 2, 3, 14, 10, 2)
            ctx.beginPath()
            ctx.moveTo(5, 13); ctx.lineTo(3, 16); ctx.lineTo(8, 13)
            ctx.stroke()
        }
        else if (name === "brand") {
            // Brand emblem S/Box
            strokeRoundRect(ctx, 2, 2, 14, 14, 3)
            ctx.beginPath()
            ctx.moveTo(6, 6); ctx.lineTo(12, 6); ctx.lineTo(6, 12); ctx.lineTo(12, 12)
            ctx.stroke()
        }
        else if (name === "trash") {
            // Trash bin icon (Matching Image #2 column header action)
            ctx.beginPath()
            ctx.moveTo(3, 5); ctx.lineTo(15, 5)
            ctx.moveTo(6, 5); ctx.lineTo(6, 15); ctx.lineTo(12, 15); ctx.lineTo(12, 5)
            ctx.moveTo(8, 3); ctx.lineTo(10, 3)
            ctx.stroke()
        }
        else if (name === "plus") {
            // Plus sign
            ctx.beginPath()
            ctx.moveTo(9, 4); ctx.lineTo(9, 14)
            ctx.moveTo(4, 9); ctx.lineTo(14, 9)
            ctx.stroke()
        }
        else if (name === "import") {
            // Import arrow icon
            ctx.beginPath()
            ctx.moveTo(9, 3); ctx.lineTo(9, 12)
            ctx.moveTo(6, 9); ctx.lineTo(9, 12); ctx.lineTo(12, 9)
            ctx.moveTo(4, 15); ctx.lineTo(14, 15)
            ctx.stroke()
        }
        else if (name === "search") {
            ctx.beginPath()
            ctx.arc(7.5, 7.5, 4, 0, 2 * Math.PI)
            ctx.stroke()
            ctx.beginPath()
            ctx.moveTo(10.5, 10.5); ctx.lineTo(15, 15)
            ctx.stroke()
        }
        else if (name === "close") {
            ctx.beginPath()
            ctx.moveTo(4, 4); ctx.lineTo(14, 14)
            ctx.moveTo(14, 4); ctx.lineTo(4, 14)
            ctx.stroke()
        }
    }
}
