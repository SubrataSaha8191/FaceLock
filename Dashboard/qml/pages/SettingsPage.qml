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
        spacing: 24

        Column {
            Text { text: "Security Configuration"; color: Theme.textPrimary; font.pixelSize: Theme.fontSizeHeader; font.bold: true }
            Text { text: "Manage biometric similarity thresholds and liveness verification settings"; color: Theme.textSecondary; font.pixelSize: Theme.fontSizeSmall }
        }

        GlowCard {
            Layout.fillWidth: true
            implicitHeight: 130
            accentGlow: Theme.glassBorder

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Cosine Similarity Threshold"
                        color: Theme.textPrimary
                        font.pixelSize: Theme.fontSizeBody
                        font.bold: true
                        Layout.fillWidth: true
                    }
                    Text {
                        text: (thresholdSlider.value * 100).toFixed(0) + "%"
                        color: Theme.accent
                        font.bold: true
                        font.pixelSize: Theme.fontSizeTitle
                    }
                }

                Slider {
                    id: thresholdSlider
                    from: 0.4; to: 0.9; value: 0.6; stepSize: 0.05
                    Layout.fillWidth: true

                    background: Rectangle {
                        implicitHeight: 6
                        radius: 3
                        color: Theme.cardHover

                        Rectangle {
                            width: thresholdSlider.visualPosition * parent.width
                            height: parent.height
                            radius: 3
                            color: Theme.accent
                        }
                    }

                    handle: Rectangle {
                        x: thresholdSlider.visualPosition * (thresholdSlider.width - width)
                        y: (thresholdSlider.height - height) / 2
                        width: 20; height: 20; radius: 10
                        color: Theme.accent
                    }
                }
            }
        }

        GlowCard {
            Layout.fillWidth: true
            implicitHeight: 80
            accentGlow: Theme.glassBorder

            RowLayout {
                anchors.fill: parent
                anchors.margins: 20

                Text {
                    text: "Anti-Spoof Liveness Detection"
                    color: Theme.textPrimary
                    font.pixelSize: Theme.fontSizeBody
                    font.bold: true
                    Layout.fillWidth: true
                }
                Switch {
                    id: livenessSwitch
                    checked: true
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            PrimaryButton {
                text: "Save Settings"
                implicitWidth: 160
                implicitHeight: 44
                onClicked: {
                    if (typeof facelockBridge !== "undefined") {
                        facelockBridge.statusMessageChanged("Settings saved successfully", true)
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }
    }
}
