import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import "../themes"

Item {
    id: root

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        RowLayout {
            Layout.fillWidth: true

            Column {
                Text { text: "Perception & Camera Diagnostics"; color: Theme.textPrimary; font.pixelSize: Theme.fontSizeHeader; font.bold: true }
                Text { text: "Real-time OpenCV frame processing & face bounding view"; color: Theme.textSecondary; font.pixelSize: Theme.fontSizeSmall }
            }

            Item { Layout.fillWidth: true }

            PrimaryButton {
                text: "Toggle Camera"
                isPrimary: false
                onClicked: {
                    if (typeof facelockBridge !== "undefined") {
                        var active = facelockBridge.getMetrics().cameraActive
                        facelockBridge.toggleCamera(!active)
                    }
                }
            }
        }

        GlowCard {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Image {
                id: liveStream
                anchors.fill: parent
                anchors.margins: 8
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

            StatusBadge {
                text: "LIVE STREAM"
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.margins: 16
            }
        }
    }
}
