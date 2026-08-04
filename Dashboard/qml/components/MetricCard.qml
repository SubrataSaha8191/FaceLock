import QtQuick
import QtQuick.Controls
import "../themes"

Rectangle {
    id: root
    property string title: "Metric"
    property string value: "0"
    property string subtext: "Active status"
    property color accentColor: Theme.primary

    implicitWidth: 200
    implicitHeight: 115
    radius: Theme.cornerRadius
    color: hoverArea.containsMouse ? Theme.surfaceElevated : Theme.surface
    border.color: hoverArea.containsMouse ? Qt.alpha(accentColor, 0.4) : Theme.surfaceBorder
    border.width: 1

    Behavior on color { ColorAnimation { duration: Theme.animNormal } }
    Behavior on border.color { ColorAnimation { duration: Theme.animNormal } }

    Column {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 4

        Text {
            text: root.value
            color: Theme.textPrimary
            font.pixelSize: Theme.fontSizeHero
            font.bold: true
        }

        Text {
            text: root.title
            color: Theme.textSecondary
            font.pixelSize: Theme.fontSizeSmall
            font.weight: Font.Medium
        }
    }

    // Top decorative curve accent (similar to reference UI card charts)
    Canvas {
        id: curveCanvas
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 35
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            ctx.beginPath()
            ctx.moveTo(10, 25)
            ctx.bezierCurveTo(width * 0.3, 5, width * 0.7, 30, width - 10, 15)
            ctx.strokeStyle = root.accentColor
            ctx.lineWidth = 2.5
            ctx.stroke()
        }
    }

    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: true
        propagateComposedEvents: true
        acceptedButtons: Qt.NoButton
    }
}
