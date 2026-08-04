import QtQuick
import QtQuick.Controls
import "../themes"

TextField {
    id: root
    property color focusBorderColor: Theme.primary

    color: Theme.textPrimary
    font.pixelSize: Theme.fontSizeBody
    placeholderTextColor: Theme.textMuted
    selectionColor: Qt.alpha(Theme.primary, 0.3)

    background: Rectangle {
        radius: Theme.cornerRadiusSmall
        color: Theme.surfaceElevated
        border.color: root.activeFocus ? root.focusBorderColor : Theme.surfaceBorder
        border.width: root.activeFocus ? 1.5 : 1

        Behavior on border.color {
            ColorAnimation { duration: Theme.animFast }
        }
    }

    leftPadding: 14
    rightPadding: 14
    topPadding: 10
    bottomPadding: 10
}
