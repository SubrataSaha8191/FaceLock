import QtQuick
import QtQuick.Controls
import "../themes"

TextField {
    id: root
    property string iconName: ""

    implicitHeight: 36
    color: Theme.textPrimary
    placeholderTextColor: Theme.textMuted
    font.pixelSize: Theme.fontSizeSmall
    leftPadding: iconName !== "" ? 34 : 12

    background: Rectangle {
        radius: Theme.cornerRadiusSmall
        color: root.activeFocus ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(1, 1, 1, 0.04)
        border.color: root.activeFocus ? Qt.rgba(1, 1, 1, 0.25) : Theme.glassBorder
        border.width: 1

        Behavior on border.color { ColorAnimation { duration: Theme.animFast } }

        VectorIcon {
            visible: root.iconName !== ""
            name: root.iconName
            iconColor: Theme.textMuted
            implicitWidth: 14
            implicitHeight: 14
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: 12
        }
    }
}
