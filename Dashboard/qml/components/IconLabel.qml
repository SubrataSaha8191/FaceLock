import QtQuick
import "../themes"

Row {
    id: root
    property string iconName: "dashboard"
    property string label: "Label"
    property color iconColor: Theme.primary
    property color textColor: Theme.textPrimary

    spacing: 10

    VectorIcon {
        name: root.iconName
        iconColor: root.iconColor
        implicitWidth: 18
        implicitHeight: 18
        anchors.verticalCenter: parent.verticalCenter
    }

    Text {
        text: root.label
        color: root.textColor
        font.pixelSize: Theme.fontSizeBody
        font.bold: true
        anchors.verticalCenter: parent.verticalCenter
    }
}
