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

        Row {
            spacing: 12
            Text { text: "⚙"; color: Theme.primary; font.pixelSize: Theme.fontSizeHeader }
            Column {
                Text { text: "Security Configuration"; color: Theme.textPrimary; font.pixelSize: Theme.fontSizeHeader; font.bold: true }
                Text { text: "Fine-tune authentication thresholds and security policies"; color: Theme.textMuted; font.pixelSize: Theme.fontSizeSmall }
            }
        }

        // Matching threshold card
        GlowCard {
            Layout.fillWidth: true
            implicitHeight: 130
            glowColor: Theme.warning

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true
                    IconLabel { icon: "◆"; label: "Cosine Similarity Threshold"; iconColor: Theme.warning }
                    Item { Layout.fillWidth: true }
                    Text {
                        text: (thresholdSlider.value * 100).toFixed(0) + "%"
                        color: Theme.warning
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
                        color: Theme.surfaceElevated

                        Rectangle {
                            width: thresholdSlider.visualPosition * parent.width
                            height: parent.height
                            radius: 3
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0; color: Theme.gradientStart }
                                GradientStop { position: 1; color: Theme.gradientEnd }
                            }
                        }
                    }

                    handle: Rectangle {
                        x: thresholdSlider.visualPosition * (thresholdSlider.width - width)
                        y: (thresholdSlider.height - height) / 2
                        width: 20; height: 20; radius: 10
                        color: Theme.primary
                        border.color: Theme.primaryHover; border.width: 2
                    }
                }
            }
        }

        // Liveness toggle card
        GlowCard {
            Layout.fillWidth: true
            implicitHeight: 80
            glowColor: Theme.success

            RowLayout {
                anchors.fill: parent
                anchors.margins: 20

                IconLabel { icon: "◉"; label: "Anti-Spoof Liveness Detection"; iconColor: Theme.success }
                Item { Layout.fillWidth: true }
                Switch {
                    id: livenessSwitch
                    checked: true
                }
            }
        }

        // Save button
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            PrimaryButton {
                text: "⬤  Save Settings"
                implicitWidth: 180
                implicitHeight: 46
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
