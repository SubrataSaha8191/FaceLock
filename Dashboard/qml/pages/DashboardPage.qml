import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import "../themes"

Item {
    id: root

    Component.onCompleted: refreshMetrics()

    function refreshMetrics() {
        if (typeof facelockBridge !== "undefined") {
            var m = facelockBridge.getMetrics()
            userCountText.text = m.registeredUsersCount.toString()
            livenessText.text = m.livenessEnabled ? "Active" : "Off"
            thresholdText.text = (m.matchingThreshold * 100).toFixed(0) + "%"
        }
    }

    ColumnLayout {
        anchors.fill: parent; anchors.margins: 20; spacing: 16

        RowLayout {
            spacing: 14; Layout.fillWidth: true

            GlowCard {
                Layout.fillWidth: true; implicitHeight: 76
                Column {
                    anchors.fill: parent; anchors.margins: 12; spacing: 4
                    Text { text: "ENROLLED USERS"; color: Theme.textMuted; font.pixelSize: 10; font.bold: true }
                    Text { id: userCountText; text: "0"; color: Theme.textPrimary; font.pixelSize: 20; font.bold: true }
                    Text { text: "Encrypted 128D Vectors"; color: Theme.textMuted; font.pixelSize: 10 }
                }
            }

            GlowCard {
                Layout.fillWidth: true; implicitHeight: 76
                Column {
                    anchors.fill: parent; anchors.margins: 12; spacing: 4
                    Text { text: "ANTI-SPOOF LIVENESS"; color: Theme.textMuted; font.pixelSize: 10; font.bold: true }
                    Text { id: livenessText; text: "Active"; color: Theme.textPrimary; font.pixelSize: 20; font.bold: true }
                    Text { text: "LBP Texture + Blink Analysis"; color: Theme.textMuted; font.pixelSize: 10 }
                }
            }

            GlowCard {
                Layout.fillWidth: true; implicitHeight: 76
                Column {
                    anchors.fill: parent; anchors.margins: 12; spacing: 4
                    Text { text: "MATCHING THRESHOLD"; color: Theme.textMuted; font.pixelSize: 10; font.bold: true }
                    Text { id: thresholdText; text: "60%"; color: Theme.textPrimary; font.pixelSize: 20; font.bold: true }
                    Text { text: "Cosine Similarity Cutoff"; color: Theme.textMuted; font.pixelSize: 10 }
                }
            }

            GlowCard {
                Layout.fillWidth: true; implicitHeight: 76
                Column {
                    anchors.fill: parent; anchors.margins: 12; spacing: 4
                    Text { text: "PAM LOCKOUT POLICY"; color: Theme.textMuted; font.pixelSize: 10; font.bold: true }
                    Text { text: "3 Retries Max"; color: Theme.textPrimary; font.pixelSize: 20; font.bold: true }
                    Text { text: "5m Lockout Timeout"; color: Theme.textMuted; font.pixelSize: 10 }
                }
            }
        }

        RowLayout {
            spacing: 14; Layout.fillWidth: true; Layout.fillHeight: true

            GlowCard {
                Layout.fillWidth: true; Layout.fillHeight: true
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 16; spacing: 12
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "Enrolled Identities"; color: Theme.textPrimary; font.pixelSize: Theme.fontSizeBody; font.bold: true }
                        Item { Layout.fillWidth: true }
                        StatusBadge { text: "AES-256 Encrypted" }
                    }
                    ScrollView {
                        Layout.fillWidth: true; Layout.fillHeight: true; clip: true
                        ListView {
                            id: userListView
                            model: typeof facelockBridge !== "undefined" ? facelockBridge.getUsers() : []
                            spacing: 6
                            delegate: UserCard {
                                width: userListView.width - 4
                                userId: modelData.userId; username: modelData.username
                                onDeleteRequested: function(uid) {
                                    if (typeof facelockBridge !== "undefined") {
                                        facelockBridge.deleteUser(uid)
                                        userListView.model = facelockBridge.getUsers()
                                        root.refreshMetrics()
                                    }
                                }
                            }
                        }
                    }
                }
            }

            GlowCard {
                implicitWidth: 320; Layout.fillHeight: true
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 16; spacing: 14
                    Text { text: "Security System Status"; color: Theme.textPrimary; font.pixelSize: Theme.fontSizeBody; font.bold: true }
                    Column {
                        spacing: 10; Layout.fillWidth: true
                        Row {
                            spacing: 8
                            VectorIcon { name: "camera"; iconColor: Theme.textSecondary; implicitWidth: 14; implicitHeight: 14 }
                            Text { text: "OpenCV Camera Bridge"; color: Theme.textPrimary; font.pixelSize: Theme.fontSizeSmall }
                        }
                        Row {
                            spacing: 8
                            VectorIcon { name: "settings"; iconColor: Theme.textSecondary; implicitWidth: 14; implicitHeight: 14 }
                            Text { text: "Haar Cascade Detector"; color: Theme.textPrimary; font.pixelSize: Theme.fontSizeSmall }
                        }
                        Row {
                            spacing: 8
                            VectorIcon { name: "logs"; iconColor: Theme.textSecondary; implicitWidth: 14; implicitHeight: 14 }
                            Text { text: "PAM Module Service"; color: Theme.textPrimary; font.pixelSize: Theme.fontSizeSmall }
                        }
                    }
                    Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: Theme.glassBorder }
                    Text { text: "System Audit Stream"; color: Theme.textPrimary; font.pixelSize: Theme.fontSizeSmall; font.bold: true }
                    Text { text: "Daemon listening on local IPC domain socket for Linux PAM events."; color: Theme.textMuted; font.pixelSize: Theme.fontSizeXs }
                    Item { Layout.fillHeight: true }
                }
            }
        }
    }

    Connections {
        target: typeof facelockBridge !== "undefined" ? facelockBridge : null
        function onUserListChanged() {
            userListView.model = facelockBridge.getUsers()
            root.refreshMetrics()
        }
    }
}
