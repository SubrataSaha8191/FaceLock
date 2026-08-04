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
            userCountMetric.value = m.registeredUsersCount.toString()
            livenessMetric.value = m.livenessEnabled ? "Enabled" : "Disabled"
            thresholdMetric.value = (m.matchingThreshold * 100).toFixed(0) + "%"
            cameraMetric.value = m.cameraActive ? "Active" : "Offline"
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 24

        // Gradient header
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 52
            color: "transparent"

            Row {
                anchors.verticalCenter: parent.verticalCenter
                spacing: 12

                Text {
                    text: "◫"
                    color: Theme.primary
                    font.pixelSize: Theme.fontSizeHeader
                }
                Column {
                    Text {
                        text: "System Overview"
                        color: Theme.textPrimary
                        font.pixelSize: Theme.fontSizeHeader
                        font.bold: true
                    }
                    Text {
                        text: "Monitor biometric system health and enrolled users"
                        color: Theme.textMuted
                        font.pixelSize: Theme.fontSizeSmall
                    }
                }
            }
        }

        // Metrics row
        RowLayout {
            spacing: 16
            Layout.fillWidth: true

            MetricCard {
                id: userCountMetric
                title: "Enrolled Users"
                icon: "◎"
                value: "0"
                accentColor: Theme.primary
                Layout.fillWidth: true
            }
            MetricCard {
                id: livenessMetric
                title: "Liveness Detection"
                icon: "◉"
                value: "Enabled"
                accentColor: Theme.success
                Layout.fillWidth: true
            }
            MetricCard {
                id: thresholdMetric
                title: "Match Threshold"
                icon: "◆"
                value: "60%"
                accentColor: Theme.warning
                Layout.fillWidth: true
            }
            MetricCard {
                id: cameraMetric
                title: "Camera Status"
                icon: "⬤"
                value: "Offline"
                accentColor: Theme.info
                Layout.fillWidth: true
            }
        }

        // Section header
        RowLayout {
            Layout.fillWidth: true
            Text {
                text: "Registered Biometric Identities"
                color: Theme.textPrimary
                font.pixelSize: Theme.fontSizeTitle
                font.bold: true
                Layout.fillWidth: true
            }
            StatusBadge {
                text: typeof facelockBridge !== "undefined"
                    ? facelockBridge.getUsers().length + " USERS" : "0 USERS"
                badgeColor: Theme.primary
            }
        }

        // User list
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ListView {
                id: userListView
                model: typeof facelockBridge !== "undefined" ? facelockBridge.getUsers() : []
                spacing: 8

                delegate: UserCard {
                    width: userListView.width - 16
                    userId: modelData.userId
                    username: modelData.username
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

    Connections {
        target: typeof facelockBridge !== "undefined" ? facelockBridge : null
        function onUserListChanged() {
            userListView.model = facelockBridge.getUsers()
            root.refreshMetrics()
        }
    }
}
