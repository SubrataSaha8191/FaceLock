import QtQuick
import QtQuick.Controls
import "../themes"

Rectangle {
    id: root
    property int currentIndex: 0
    signal pageSelected(int index)

    width: 240
    color: Theme.surface
    border.color: Theme.surfaceBorder
    border.width: 1

    Column {
        anchors.fill: parent
        spacing: 0

        // Brand Header
        Item {
            width: parent.width
            height: 72

            Row {
                anchors.centerIn: parent
                spacing: 10

                Text {
                    text: "◉"
                    color: Theme.primary
                    font.pixelSize: 22
                    anchors.verticalCenter: parent.verticalCenter
                }

                Column {
                    anchors.verticalCenter: parent.verticalCenter
                    Text {
                        text: "FaceLock"
                        color: Theme.textPrimary
                        font.pixelSize: Theme.fontSizeTitle
                        font.bold: true
                        font.letterSpacing: 0.5
                    }
                    Text {
                        text: "Biometric Security"
                        color: Theme.textMuted
                        font.pixelSize: Theme.fontSizeXs
                        font.letterSpacing: 0.8
                    }
                }
            }
        }

        // Gradient separator
        Rectangle {
            width: parent.width - 32
            height: 1
            anchors.horizontalCenter: parent.horizontalCenter
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: "transparent" }
                GradientStop { position: 0.5; color: Theme.surfaceBorder }
                GradientStop { position: 1.0; color: "transparent" }
            }
        }

        Item { width: 1; height: 12 }

        // Section label
        Text {
            text: "NAVIGATION"
            color: Theme.textMuted
            font.pixelSize: Theme.fontSizeXs
            font.bold: true
            font.letterSpacing: 1.2
            leftPadding: 24
        }

        Item { width: 1; height: 8 }

        Repeater {
            model: [
                { label: "Dashboard",    icon: "◫" },
                { label: "Enrollment",   icon: "◎" },
                { label: "Camera Test",  icon: "◉" },
                { label: "Settings",     icon: "⚙" },
                { label: "Audit Logs",   icon: "☰" }
            ]

            Button {
                required property int index
                required property var modelData

                width: parent.width - 16
                height: 44
                anchors.horizontalCenter: parent.horizontalCenter

                background: Rectangle {
                    radius: Theme.cornerRadiusSmall
                    color: root.currentIndex === index
                        ? Qt.alpha(Theme.primary, 0.12)
                        : (hovered ? Qt.alpha(Theme.surfaceBorder, 0.4) : "transparent")

                    Behavior on color { ColorAnimation { duration: Theme.animFast } }

                    // Active indicator bar
                    Rectangle {
                        width: 3
                        height: parent.height - 12
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        radius: 1.5
                        color: Theme.primary
                        visible: root.currentIndex === index
                    }
                }

                contentItem: Row {
                    spacing: 12
                    leftPadding: 18

                    Text {
                        text: modelData.icon
                        color: root.currentIndex === index ? Theme.primary : Theme.textSecondary
                        font.pixelSize: Theme.fontSizeBody
                        anchors.verticalCenter: parent.verticalCenter

                        Behavior on color { ColorAnimation { duration: Theme.animFast } }
                    }

                    Text {
                        text: modelData.label
                        color: root.currentIndex === index ? Theme.primary : Theme.textPrimary
                        font.pixelSize: Theme.fontSizeBody
                        font.weight: root.currentIndex === index ? Font.DemiBold : Font.Normal
                        anchors.verticalCenter: parent.verticalCenter

                        Behavior on color { ColorAnimation { duration: Theme.animFast } }
                    }
                }

                onClicked: {
                    root.currentIndex = index
                    root.pageSelected(index)
                }
            }
        }
    }
}
