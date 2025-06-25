import React, { useState, useMemo, useRef } from 'react';
import { 
  Table, 
  Button, 
  Modal, 
  Input, 
  message, 
  Tag, 
  Space, 
  Tooltip,
  Form,
  Avatar,
  Select,
  DatePicker,
  Card,
  Row,
  Col,
  Switch,
  Tabs
} from 'antd';
import { 
  CheckOutlined, 
  CloseOutlined,
  SyncOutlined, 
  ExclamationCircleOutlined,
  LinkOutlined,
  UserOutlined,
  SearchOutlined,
  FilterOutlined,
  ClearOutlined,
  DashboardOutlined,
  TableOutlined,
  QuestionCircleOutlined,
  FileExcelOutlined
} from '@ant-design/icons';
import moment from 'moment';
import { useFilterPersistence } from '../hooks/useFilterPersistence';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import FilterPresets from './FilterPresets';
import BulkOperations from './BulkOperations';
import StatusIndicator from './StatusIndicator';
import DashboardWidgets from './DashboardWidgets';
import CSVExportModal from './CSVExportModal';

const { TextArea } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { TabPane } = Tabs;

const AlertTable = ({ alerts, loading, onAcknowledge, onResolve, onSync, error }) => {
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [acknowledgeModalVisible, setAcknowledgeModalVisible] = useState(false);
  const [resolveModalVisible, setResolveModalVisible] = useState(false);
  const [csvExportModalVisible, setCsvExportModalVisible] = useState(false);
  const [acknowledgeForm] = Form.useForm();
  const [resolveForm] = Form.useForm();
  const [currentView, setCurrentView] = useState('table');
  const searchInputRef = useRef(null);
  
  // Use persistent filters
  const {
    filters,
    updateFilter,
    clearFilters,
    showAdvancedFilters,
    setShowAdvancedFilters
  } = useFilterPersistence({
    alertName: '',
    cluster: '',
    severity: [],
    grafanaStatus: [],
    jiraStatus: [],
    assignee: '',
    acknowledgedBy: '',
    resolvedBy: '',
    dateRange: null,
    jiraIssueKey: ''
  });

  // Keyboard shortcuts
  const {
    shortcutsEnabled,
    helpVisible,
    setHelpVisible,
    renderHelpModal
  } = useKeyboardShortcuts({
    onRefresh: onSync,
    onSelectAll: () => {
      const selectableAlerts = filteredAlerts
        .filter(alert => alert.jira_status !== 'resolved' && alert.grafana_status !== 'resolved')
        .map(alert => alert.id);
      setSelectedRowKeys(selectableAlerts);
      message.success(`Selected ${selectableAlerts.length} alerts`);
    },
    onClearSelection: () => {
      setSelectedRowKeys([]);
      message.success('Selection cleared');
    },
    onAcknowledge: () => {
      if (selectedRowKeys.length > 0) {
        setAcknowledgeModalVisible(true);
      }
    },
    onResolve: () => {
      if (selectedRowKeys.length > 0) {
        setResolveModalVisible(true);
      }
    },
    onToggleFilters: () => {
      setShowAdvancedFilters(!showAdvancedFilters);
      message.success(showAdvancedFilters ? 'Advanced filters hidden' : 'Advanced filters shown');
    },
    onFocusSearch: () => {
      if (searchInputRef.current) {
        searchInputRef.current.focus();
        message.success('Search focused');
      }
    },
    selectedCount: selectedRowKeys.length
  });

  // Get unique values for dropdowns
  const uniqueValues = useMemo(() => {
    return {
      clusters: [...new Set(alerts.map(alert => alert.cluster).filter(Boolean))],
      severities: [...new Set(alerts.map(alert => alert.severity).filter(Boolean))],
      grafanaStatuses: [...new Set(alerts.map(alert => alert.grafana_status).filter(Boolean))],
      jiraStatuses: [...new Set(alerts.map(alert => alert.jira_status).filter(Boolean))],
      assignees: [...new Set(alerts.map(alert => alert.jira_assignee).filter(Boolean))],
      acknowledgedBy: [...new Set(alerts.map(alert => alert.acknowledged_by).filter(Boolean))],
      resolvedBy: [...new Set(alerts.map(alert => alert.resolved_by).filter(Boolean))]
    };
  }, [alerts]);

  // Filter alerts based on current filters
  const filteredAlerts = useMemo(() => {
    return alerts.filter(alert => {
      // Text filters
      if (filters.alertName && !alert.alert_name?.toLowerCase().includes(filters.alertName.toLowerCase())) {
        return false;
      }
      if (filters.cluster && !alert.cluster?.toLowerCase().includes(filters.cluster.toLowerCase())) {
        return false;
      }
      if (filters.assignee && !alert.jira_assignee?.toLowerCase().includes(filters.assignee.toLowerCase())) {
        return false;
      }
      if (filters.acknowledgedBy && !alert.acknowledged_by?.toLowerCase().includes(filters.acknowledgedBy.toLowerCase())) {
        return false;
      }
      if (filters.resolvedBy && !alert.resolved_by?.toLowerCase().includes(filters.resolvedBy.toLowerCase())) {
        return false;
      }
      if (filters.jiraIssueKey && !alert.jira_issue_key?.toLowerCase().includes(filters.jiraIssueKey.toLowerCase())) {
        return false;
      }

      // Array filters
      if (filters.severity.length > 0 && !filters.severity.includes(alert.severity)) {
        return false;
      }
      if (filters.grafanaStatus.length > 0 && !filters.grafanaStatus.includes(alert.grafana_status)) {
        return false;
      }
      if (filters.jiraStatus.length > 0 && !filters.jiraStatus.includes(alert.jira_status)) {
        return false;
      }

      // Date range filter
      if (filters.dateRange && filters.dateRange.length === 2) {
        const alertDate = moment(alert.created_at);
        const [startDate, endDate] = filters.dateRange;
        if (!alertDate.isBetween(startDate, endDate, 'day', '[]')) {
          return false;
        }
      }

      return true;
    });
  }, [alerts, filters]);

  // Clear all filters
  const handleClearFilters = () => {
    clearFilters();
    setSelectedRowKeys([]);
  };

  // Apply filter preset
  const handleApplyPreset = (presetFilters) => {
    clearFilters();
    Object.entries(presetFilters).forEach(([key, value]) => {
      updateFilter(key, value);
    });
    setSelectedRowKeys([]);
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'red',
      warning: 'orange',
      info: 'blue',
      unknown: 'default',
    };
    return colors[severity?.toLowerCase()] || 'default';
  };

  const getStatusColor = (status) => {
    const colors = {
      active: 'red',
      resolved: 'green',
      open: 'orange',
      acknowledged: 'blue',
      closed: 'green',
    };
    return colors[status?.toLowerCase()] || 'default';
  };

  const columns = [
    {
      title: 'Alert Name',
      dataIndex: 'alert_name',
      key: 'alert_name',
      sorter: (a, b) => (a.alert_name || '').localeCompare(b.alert_name || ''),
      sortDirections: ['ascend', 'descend'],
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {record.cluster && `Cluster: ${record.cluster}`}
            {record.pod && ` | Pod: ${record.pod}`}
          </div>
        </div>
      ),
    },
    {
      title: 'Cluster',
      dataIndex: 'cluster',
      key: 'cluster',
      sorter: (a, b) => (a.cluster || '').localeCompare(b.cluster || ''),
      sortDirections: ['ascend', 'descend'],
      render: (text) => text || '-',
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      sorter: (a, b) => {
        const severityOrder = { critical: 4, warning: 3, info: 2, unknown: 1 };
        return (severityOrder[a.severity] || 0) - (severityOrder[b.severity] || 0);
      },
      sortDirections: ['ascend', 'descend'],
      render: (severity) => (
        <Tag color={getSeverityColor(severity)}>
          {severity?.toUpperCase() || 'UNKNOWN'}
        </Tag>
      ),
    },
    {
      title: 'Summary',
      dataIndex: 'summary',
      key: 'summary',
      ellipsis: true,
      sorter: (a, b) => (a.summary || '').localeCompare(b.summary || ''),
      sortDirections: ['ascend', 'descend'],
      render: (text) => (
        <Tooltip title={text}>
          {text || 'No summary available'}
        </Tooltip>
      ),
    },
    {
      title: 'Grafana Status',
      dataIndex: 'grafana_status',
      key: 'grafana_status',
      sorter: (a, b) => (a.grafana_status || '').localeCompare(b.grafana_status || ''),
      sortDirections: ['ascend', 'descend'],
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {status?.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Jira Status',
      dataIndex: 'jira_status',
      key: 'jira_status',
      sorter: (a, b) => (a.jira_status || '').localeCompare(b.jira_status || ''),
      sortDirections: ['ascend', 'descend'],
      render: (status, record) => (
        <div>
          <Tag color={getStatusColor(status)}>
            {status?.toUpperCase()}
          </Tag>
          {!record.jira_issue_key && (
            <div style={{ fontSize: '10px', color: '#999', marginTop: '2px' }}>
              No Jira ticket
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Assignee / Acknowledged By',
      key: 'assignee_info',
      sorter: (a, b) => {
        const aName = a.jira_assignee || a.acknowledged_by || a.resolved_by || '';
        const bName = b.jira_assignee || b.acknowledged_by || b.resolved_by || '';
        return aName.localeCompare(bName);
      },
      sortDirections: ['ascend', 'descend'],
      render: (_, record) => (
        <div>
          {record.jira_assignee && (
            <div style={{ marginBottom: '4px' }}>
              <Avatar size="small" icon={<UserOutlined />} style={{ marginRight: '4px' }} />
              <Tooltip title={`Jira Assignee: ${record.jira_assignee_email || 'No email'}`}>
                <span style={{ fontSize: '12px', color: '#1890ff' }}>
                  {record.jira_assignee}
                </span>
              </Tooltip>
            </div>
          )}
          {record.acknowledged_by && (
            <div>
              <Tag icon={<CheckOutlined />} color="blue" size="small">
                Ack: {record.acknowledged_by}
              </Tag>
              {record.acknowledged_at && (
                <div style={{ fontSize: '10px', color: '#999' }}>
                  {moment(record.acknowledged_at).format('MM/DD HH:mm')}
                </div>
              )}
            </div>
          )}
          {record.resolved_by && (
            <div style={{ marginTop: '4px' }}>
              <Tag icon={<CloseOutlined />} color="green" size="small">
                Resolved: {record.resolved_by}
              </Tag>
              {record.resolved_at && (
                <div style={{ fontSize: '10px', color: '#999' }}>
                  {moment(record.resolved_at).format('MM/DD HH:mm')}
                </div>
              )}
            </div>
          )}
          {!record.jira_assignee && !record.acknowledged_by && !record.resolved_by && (
            <span style={{ color: '#ccc', fontSize: '12px' }}>Unassigned</span>
          )}
        </div>
      ),
    },
    {
      title: 'Jira Issue',
      dataIndex: 'jira_issue_key',
      key: 'jira_issue_key',
      sorter: (a, b) => (a.jira_issue_key || '').localeCompare(b.jira_issue_key || ''),
      sortDirections: ['ascend', 'descend'],
      render: (issueKey, record) => (
        issueKey ? (
          <Button
            type="link"
            size="small"
            icon={<LinkOutlined />}
            onClick={() => window.open(record.jira_issue_url, '_blank')}
          >
            {issueKey}
          </Button>
        ) : (
          <Tooltip title="Jira ticket will be created by Grafana integration">
            <span style={{ color: '#ccc', fontSize: '12px' }}>Pending ticket creation</span>
          </Tooltip>
        )
      ),
    },
    {
      title: 'Started At',
      dataIndex: 'started_at',
      key: 'started_at',
      sorter: (a, b) => {
        const dateA = moment(a.started_at);
        const dateB = moment(b.started_at);
        return dateA.isBefore(dateB) ? -1 : dateA.isAfter(dateB) ? 1 : 0;
      },
      sortDirections: ['ascend', 'descend'],
      defaultSortOrder: 'descend',
      render: (date) => date ? moment(date).format('YYYY-MM-DD HH:mm:ss') : 'N/A',
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      sorter: (a, b) => {
        const dateA = moment(a.created_at);
        const dateB = moment(b.created_at);
        return dateA.isBefore(dateB) ? -1 : dateA.isAfter(dateB) ? 1 : 0;
      },
      sortDirections: ['ascend', 'descend'],
      render: (date) => date ? moment(date).format('YYYY-MM-DD HH:mm:ss') : 'N/A',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          {record.generator_url && (
            <Button
              type="link"
              size="small"
              onClick={() => window.open(record.generator_url, '_blank')}
            >
              View in Grafana
            </Button>
          )}
        </Space>
      ),
    },
  ];

  const handleAcknowledge = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Please select alerts to acknowledge');
      return;
    }

    try {
      const values = await acknowledgeForm.validateFields();
      const success = await onAcknowledge(selectedRowKeys, values.note, values.acknowledged_by);
      if (success) {
        message.success(`Successfully acknowledged ${selectedRowKeys.length} alert${selectedRowKeys.length > 1 ? 's' : ''}`);
        setSelectedRowKeys([]);
        setAcknowledgeModalVisible(false);
        acknowledgeForm.resetFields();
      } else {
        message.error('Failed to acknowledge alerts');
      }
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const handleResolve = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Please select alerts to resolve');
      return;
    }

    try {
      const values = await resolveForm.validateFields();
      const success = await onResolve(selectedRowKeys, values.note, values.resolved_by);
      if (success) {
        message.success(`Successfully resolved ${selectedRowKeys.length} alert${selectedRowKeys.length > 1 ? 's' : ''}`);
        setSelectedRowKeys([]);
        setResolveModalVisible(false);
        resolveForm.resetFields();
      } else {
        message.error('Failed to resolve alerts');
      }
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const unacknowledgedCount = filteredAlerts.filter(
    alert => alert.jira_status !== 'acknowledged' && alert.jira_status !== 'resolved' && alert.grafana_status === 'active'
  ).length;

  const unresolvedCount = filteredAlerts.filter(
    alert => alert.jira_status !== 'resolved' && alert.grafana_status === 'active'
  ).length;

  const withoutJiraTickets = filteredAlerts.filter(
    alert => !alert.jira_issue_key && alert.grafana_status === 'active'
  ).length;

  const totalFilteredCount = filteredAlerts.length;
  const totalCount = alerts.length;

  return (
    <div>
      {/* Status Indicator */}
      <StatusIndicator
        alerts={alerts}
        loading={loading}
        error={error}
        onRefresh={onSync}
        filteredCount={totalFilteredCount}
        selectedCount={selectedRowKeys.length}
      />

      {/* Main Content Tabs */}
      <Tabs 
        activeKey={currentView}
        onChange={setCurrentView}
        type="card"
        tabBarExtraContent={
          <Space>
            <Tooltip title="Export to CSV">
              <Button 
                icon={<FileExcelOutlined />}
                onClick={() => setCsvExportModalVisible(true)}
              >
                Export CSV
              </Button>
            </Tooltip>
            <Tooltip title="Keyboard shortcuts (Shift + H)">
              <Button 
                size="small" 
                icon={<QuestionCircleOutlined />}
                onClick={() => setHelpVisible(true)}
              />
            </Tooltip>
          </Space>
        }
      >
        <TabPane 
          tab={
            <span>
              <DashboardOutlined />
              Dashboard
            </span>
          } 
          key="dashboard"
        >
          <DashboardWidgets alerts={filteredAlerts} loading={loading} />
        </TabPane>

        <TabPane 
          tab={
            <span>
              <TableOutlined />
              Alert Table
              {totalFilteredCount !== totalCount && (
                <Tag size="small" style={{ marginLeft: 8 }}>
                  {totalFilteredCount}/{totalCount}
                </Tag>
              )}
            </span>
          } 
          key="table"
        >
          {/* Alert Summary */}
          {withoutJiraTickets > 0 && (
            <Card 
              size="small" 
              style={{ marginBottom: 16, backgroundColor: '#fff7e6', border: '1px solid #ffd591' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', fontSize: '14px' }}>
                <ExclamationCircleOutlined style={{ color: '#fa8c16', marginRight: 8 }} />
                <span>
                  <strong>{withoutJiraTickets}</strong> alert{withoutJiraTickets > 1 ? 's' : ''} waiting for Jira ticket creation by Grafana integration
                </span>
              </div>
            </Card>
          )}

          {/* Filter Panel */}
          <Card 
            title={
              <Space>
                <FilterOutlined />
                Filters & Search
                <Tag color={totalFilteredCount !== totalCount ? 'blue' : 'default'}>
                  {totalFilteredCount} of {totalCount} alerts
                </Tag>
              </Space>
            }
            extra={
              <Space>
                <Switch
                  checkedChildren="Advanced"
                  unCheckedChildren="Simple"
                  checked={showAdvancedFilters}
                  onChange={setShowAdvancedFilters}
                />
                <Button 
                  icon={<ClearOutlined />} 
                  onClick={handleClearFilters}
                  disabled={Object.values(filters).every(val => !val || (Array.isArray(val) && val.length === 0))}
                >
                  Clear Filters
                </Button>
              </Space>
            }
            style={{ marginBottom: 16 }}
          >
            {/* Quick Filter Presets */}
            <div style={{ marginBottom: 16, paddingBottom: 16, borderBottom: '1px solid #f0f0f0' }}>
              <div style={{ marginBottom: 8, fontSize: '12px', color: '#666', fontWeight: 'bold' }}>
                QUICK FILTERS
              </div>
              <FilterPresets onApplyPreset={handleApplyPreset} currentFilters={filters} />
            </div>
            <Row gutter={[16, 16]}>
              {/* Basic Filters */}
              <Col xs={24} sm={12} md={8} lg={6}>
                <Input
                  ref={searchInputRef}
                  placeholder="Search alert name..."
                  prefix={<SearchOutlined />}
                  value={filters.alertName}
                  onChange={(e) => updateFilter('alertName', e.target.value)}
                  allowClear
                />
              </Col>
              
              <Col xs={24} sm={12} md={8} lg={6}>
                <Select
                  mode="multiple"
                  placeholder="Filter by severity"
                  value={filters.severity}
                  onChange={(value) => updateFilter('severity', value)}
                  style={{ width: '100%' }}
                  allowClear
                >
                  {uniqueValues.severities.map(severity => (
                    <Option key={severity} value={severity}>
                      <Tag color={getSeverityColor(severity)} size="small">
                        {severity?.toUpperCase()}
                      </Tag>
                    </Option>
                  ))}
                </Select>
              </Col>
              
              <Col xs={24} sm={12} md={8} lg={6}>
                <Select
                  mode="multiple"
                  placeholder="Filter by Grafana status"
                  value={filters.grafanaStatus}
                  onChange={(value) => updateFilter('grafanaStatus', value)}
                  style={{ width: '100%' }}
                  allowClear
                >
                  {uniqueValues.grafanaStatuses.map(status => (
                    <Option key={status} value={status}>
                      <Tag color={getStatusColor(status)} size="small">
                        {status?.toUpperCase()}
                      </Tag>
                    </Option>
                  ))}
                </Select>
              </Col>
              
              <Col xs={24} sm={12} md={8} lg={6}>
                <Select
                  mode="multiple"
                  placeholder="Filter by Jira status"
                  value={filters.jiraStatus}
                  onChange={(value) => updateFilter('jiraStatus', value)}
                  style={{ width: '100%' }}
                  allowClear
                >
                  {uniqueValues.jiraStatuses.map(status => (
                    <Option key={status} value={status}>
                      <Tag color={getStatusColor(status)} size="small">
                        {status?.toUpperCase()}
                      </Tag>
                    </Option>
                  ))}
                </Select>
              </Col>

              {/* Advanced Filters */}
              {showAdvancedFilters && (
                <>
                  <Col xs={24} sm={12} md={8} lg={6}>
                    <Input
                      placeholder="Search cluster..."
                      prefix={<SearchOutlined />}
                      value={filters.cluster}
                      onChange={(e) => updateFilter('cluster', e.target.value)}
                      allowClear
                    />
                  </Col>
                  
                  <Col xs={24} sm={12} md={8} lg={6}>
                    <Input
                      placeholder="Search Jira assignee..."
                      prefix={<UserOutlined />}
                      value={filters.assignee}
                      onChange={(e) => updateFilter('assignee', e.target.value)}
                      allowClear
                    />
                  </Col>
                  
                  <Col xs={24} sm={12} md={8} lg={6}>
                    <Input
                      placeholder="Search acknowledged by..."
                      prefix={<CheckOutlined />}
                      value={filters.acknowledgedBy}
                      onChange={(e) => updateFilter('acknowledgedBy', e.target.value)}
                      allowClear
                    />
                  </Col>
                  
                  <Col xs={24} sm={12} md={8} lg={6}>
                    <Input
                      placeholder="Search resolved by..."
                      prefix={<CloseOutlined />}
                      value={filters.resolvedBy}
                      onChange={(e) => updateFilter('resolvedBy', e.target.value)}
                      allowClear
                    />
                  </Col>
                  
                  <Col xs={24} sm={12} md={8} lg={6}>
                    <Input
                      placeholder="Search Jira issue..."
                      prefix={<LinkOutlined />}
                      value={filters.jiraIssueKey}
                      onChange={(e) => updateFilter('jiraIssueKey', e.target.value)}
                      allowClear
                    />
                  </Col>
                  
                  <Col xs={24} sm={12} md={8} lg={6}>
                    <RangePicker
                      placeholder={['Start date', 'End date']}
                      value={filters.dateRange}
                      onChange={(dates) => updateFilter('dateRange', dates)}
                      style={{ width: '100%' }}
                      allowClear
                    />
                  </Col>
                </>
              )}
            </Row>
          </Card>

          {/* Action Bar */}
          <div style={{ marginBottom: 16 }}>
            <Space wrap>
              <Button
                type="primary"
                icon={<CheckOutlined />}
                onClick={() => setAcknowledgeModalVisible(true)}
                disabled={selectedRowKeys.length === 0}
              >
                Acknowledge in Jira ({selectedRowKeys.length})
              </Button>
              <Button
                type="primary"
                danger
                icon={<CloseOutlined />}
                onClick={() => setResolveModalVisible(true)}
                disabled={selectedRowKeys.length === 0}
              >
                Resolve in Jira ({selectedRowKeys.length})
              </Button>

              <BulkOperations
                selectedAlerts={selectedRowKeys}
                onAcknowledge={onAcknowledge}
                onResolve={onResolve}
                onClearSelection={() => setSelectedRowKeys([])}
                alerts={alerts}
              />

              <Button
                icon={<SyncOutlined />}
                onClick={onSync}
                loading={loading}
              >
                Sync Alerts
              </Button>

              <div style={{ marginLeft: 16 }}>
                <Space>
                  <Tag color="orange" icon={<ExclamationCircleOutlined />}>
                    {unacknowledgedCount} Unacknowledged
                  </Tag>
                  <Tag color="red" icon={<ExclamationCircleOutlined />}>
                    {unresolvedCount} Unresolved
                  </Tag>
                  {withoutJiraTickets > 0 && (
                    <Tag color="gold" icon={<ExclamationCircleOutlined />}>
                      {withoutJiraTickets} No Jira Ticket
                    </Tag>
                  )}
                  {totalFilteredCount !== totalCount && (
                    <Tag color="blue" icon={<FilterOutlined />}>
                      Filtered: {totalFilteredCount}/{totalCount}
                    </Tag>
                  )}
                </Space>
              </div>
            </Space>
          </div>

          <Table
            columns={columns}
            dataSource={filteredAlerts}
            rowKey="id"
            rowSelection={{
              selectedRowKeys,
              onChange: setSelectedRowKeys,
              getCheckboxProps: (record) => ({
                disabled: record.jira_status === 'resolved' || record.grafana_status === 'resolved',
              }),
            }}
            loading={loading}
            pagination={{
              pageSize: 50,
              showSizeChanger: true,
              pageSizeOptions: ['10', '25', '50', '100', '200'],
              showQuickJumper: true,
              showTotal: (total, range) => 
                `${range[0]}-${range[1]} of ${total} alerts${totalFilteredCount !== totalCount ? ` (filtered from ${totalCount})` : ''}`,
            }}
            scroll={{ x: 1600 }}
            size="small"
          />
        </TabPane>
      </Tabs>

      {/* CSV Export Modal */}
      <CSVExportModal
        visible={csvExportModalVisible}
        onCancel={() => setCsvExportModalVisible(false)}
        alerts={filteredAlerts}
      />

      {/* Keyboard Shortcuts Help Modal */}
      {renderHelpModal()}

      <Modal
        title="Acknowledge Alerts in Jira"
        open={acknowledgeModalVisible}
        onOk={handleAcknowledge}
        onCancel={() => {
          setAcknowledgeModalVisible(false);
          acknowledgeForm.resetFields();
        }}
        okText="Acknowledge"
      >
        <p>Are you sure you want to acknowledge {selectedRowKeys.length} alert(s) in Jira?</p>
        <p>This will transition the existing Jira issues to the acknowledged status.</p>
        <Form form={acknowledgeForm} layout="vertical">
          <Form.Item
            name="acknowledged_by"
            label="Your Name"
            rules={[{ required: true, message: 'Please enter your name' }]}
            initialValue={localStorage.getItem('alertManager_username') || ''}
          >
            <Input placeholder="Enter your name" />
          </Form.Item>
          <Form.Item name="note" label="Note (optional)">
            <TextArea
              placeholder="Add a note (optional)"
              rows={3}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="Resolve Alerts in Jira"
        open={resolveModalVisible}
        onOk={handleResolve}
        onCancel={() => {
          setResolveModalVisible(false);
          resolveForm.resetFields();
        }}
        okText="Resolve"
        okButtonProps={{ danger: true }}
      >
        <p>Are you sure you want to resolve {selectedRowKeys.length} alert(s) in Jira?</p>
        <p>This will transition the existing Jira issues to the resolved status and mark them as resolved in the system.</p>
        <Form form={resolveForm} layout="vertical">
          <Form.Item
            name="resolved_by"
            label="Your Name"
            rules={[{ required: true, message: 'Please enter your name' }]}
            initialValue={localStorage.getItem('alertManager_username') || ''}
          >
            <Input placeholder="Enter your name" />
          </Form.Item>
          <Form.Item name="note" label="Resolution Note (optional)">
            <TextArea
              placeholder="Add a resolution note (optional)"
              rows={3}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AlertTable;