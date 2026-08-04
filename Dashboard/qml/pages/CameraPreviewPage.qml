import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import "../themes"

Item {
    id: root

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 20

        RowLayout {
            Layout.fillWidth: true

            Row {
                spacing: 12
                Layout.fillWidth: true
                Text { text: "◉"; color: Theme.primary; font.pixelSize: Theme.fontSizeHeader }
                Column {
                    Text { text: "Camera & Perception"; color: Theme.textPrimary; font.pixelSize: Theme.fontSizeHeader; font.bold: true }
                    Text { text: "Live diagnostic feed with face detection overlay"; color: Theme.textMuted; font.pixelSize: Theme.fontSizeSmall }
                }
            }

            PrimaryButton {
                text: "⏻  Toggle Camera"
                onClicked: {
                    if (typeof facelockBridge !== "undefined") {
                        var active = facelockBridge.getMetrics().cameraActive
                        facelockBridge.toggleCamera(!active)
                    }
                }
            }
        }

        // Camera viewport
        GlowCard {
            Layout.fillWidth: true
            Layout.fillHeight: true
            glowColor: Theme.success

            Image {
                id: liveStream
                anchors.fill: parent
                anchors.margins: 6
                fillMode: Image.PreserveAspectFit
                source: "image://livecamera/frame"
                cache: false

                Connections {
                    target: typeof facelockBridge !== "undefined" ? facelockBridge : null
                    function onCameraFrameUpdated() {
                        liveStream.source = "image://livecamera/frame?" + Math.random()
                    }
                }
            }

            // Scan line animation overlay
            Rectangle {
                id: scanLine
                width: parent.width - 12
                height: 2
                anchors.horizontalCenter: parent.horizontalCenter
                color: Qt.alpha(Theme.primary, 0.4)
                radius: 1

                SequentialAnimation on y {
                    loops: Animation.Infinite
                    NumberAnimation { from: 6; to: root.height - 80; duration: 2500; easing.type: Easing.InOutSine }
                    NumberAnimation { from: root.height - 80; to: 6; duration: 2500; easing.type: Easing.InOutSine }
                }
            }

            StatusBadge {
                text: "LIVE STREAM"
                badgeColor: Theme.success
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.margins: 14
            }

            StatusBadge {
                text: "30 FPS"
                badgeColor: Theme.info
                anchors.top: parent.top
                anchors.right: parent.right
                anchors.margins: 14
            }
        }
    }
}
