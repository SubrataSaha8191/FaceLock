import QtQuick
import QtQuick.Controls
import "../themes"

Rectangle {
    id: root
    property string title: "Metric"
    property string value: "0"
    property string icon: "◆"
    property color accentColor: Theme.primary

    implicitWidth: 200
    implicitHeight: 110
    radius: Theme.cornerRadius
    color: Theme.surface
    border.color: cardHover.containsMouse ? Qt.alpha(accentColor, 0.5) : Theme.surfaceBorder
    border.width: cardHover.containsMouse ? 1.5 : 1

    Behavior on border.color { ColorAnimation { duration: Theme.animNormal } }

    // Gradient shimmer top edge
    Rectangle {
        width: parent.width
        height: 3
        anchors.top: parent.top
        radius: Theme.cornerRadius
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: root.accentColor }
            GradientStop { position: 1.0; color: Qt.alpha(root.accentColor, 0.2) }
        }
    }

    Column {
        anchors.fill: parent
        anchors.margins: 16
        anchors.topMargin: 20
        spacing: 6

        Row {
            spacing: 8
            Text {
                text: root.icon
                color: root.accentColor
                font.pixelSize: Theme.fontSizeSmall
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                text: root.title
                color: Theme.textSecondary
                font.pixelSize: Theme.fontSizeSmall
                font.weight: Font.Medium
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        Text {
            text: root.value
            color: Theme.textPrimary
            font.pixelSize: Theme.fontSizeHero
            font.bold: true
        }
    }

    MouseArea {
        id: cardHover
        anchors.fill: parent
        hoverEnabled: true
        propagateComposedEvents: true
        acceptedButtons: Qt.NoButton
    }
}
