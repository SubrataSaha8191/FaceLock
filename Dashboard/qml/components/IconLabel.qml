import QtQuick
import "../themes"

Row {
    id: root
    property string icon: "●"
    property string label: ""
    property color iconColor: Theme.primary
    property int fontSize: Theme.fontSizeBody

    spacing: 10

    Text {
        text: root.icon
        color: root.iconColor
        font.pixelSize: root.fontSize + 2
        anchors.verticalCenter: parent.verticalCenter
    }

    Text {
        text: root.label
        color: Theme.textPrimary
        font.pixelSize: root.fontSize
        anchors.verticalCenter: parent.verticalCenter
    }
}
