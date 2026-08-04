import QtQuick
import QtQuick.Controls
import "../themes"

Button {
    id: root
    property bool isPrimary: true
    property bool isOutlined: false

    implicitWidth: 120
    implicitHeight: 36

    scale: root.pressed ? 0.96 : (root.hovered ? 1.02 : 1.0)
    Behavior on scale { NumberAnimation { duration: Theme.animFast; easing.type: Easing.OutCubic } }

    background: Rectangle {
        radius: Theme.cornerRadiusSmall
        color: root.isPrimary
            ? (root.hovered ? "#E5E7EB" : "#FFFFFF")
            : (root.hovered ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(1, 1, 1, 0.06))

        border.color: root.isPrimary ? "transparent" : Theme.glassBorder
        border.width: 1

        Behavior on color { ColorAnimation { duration: Theme.animFast } }
    }

    contentItem: Text {
        text: root.text
        color: root.isPrimary ? "#0F1013" : Theme.textPrimary
        font.pixelSize: Theme.fontSizeSmall
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
