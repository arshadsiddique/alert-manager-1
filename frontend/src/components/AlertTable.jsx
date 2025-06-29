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
  Tabs,
  Badge,
  Progress,
  Alert
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
  FileExcelOutlined,
  ApiOutlined,
  EyeOutlined,
  InfoCircleOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  FireOutlined,
  WarningOutlined
} from '@ant-design/icons';
import moment from 'moment';

const { TextArea } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { TabPane } = Tabs;

const AlertTable = ({ alerts, loading, onAcknowledge, onResolve, onSync, error }) => {
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [acknowledgeModalVisible, setAcknowledgeModalVisible] = useState(false);
  const [resolveModalVisible, setResolveModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [acknowledgeForm] = Form.useForm();
  const [resolveForm] = Form.useForm();
  const [currentView, setCurrentView] = useState('table');
  const searchInputRef = useRef(null);
  
  // Filters state
  const [filters, setFilters] = useState({
    alertName: '',
    cluster: '',
    severity: [],
    grafanaStatus: [],
    jsmPriority: [],
    jsmStatus: [],
    matchType: [],
    owner: '',
    acknowledgedBy: '',
    resolvedBy: '',
    dateRange: null
  });
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  // Get unique values for dropdowns
  const uniqueValues = useMemo(() => {
    return {
      clusters: [...new Set(alerts.map(alert => alert.cluster).filter(Boolean))],
      severities: [...new Set(alerts.map(alert => alert.severity).filter(Boolean))],
      grafanaStatuses: [...new Set(alerts.map(alert => alert.grafana_status).filter(Boolean))],
      jsmStatuses: [...new Set(alerts.map(alert => alert.jsm_status).filter(Boolean))],
      jsmPriorities: [...new Set(alerts.map(alert => alert.jsm_priority).filter(Boolean))].sort(),
      matchTypes: [...new Set(alerts.map(alert => alert.match_type).filter(Boolean))],
      owners: [...new Set(alerts.map(alert => alert.jsm_owner).filter(Boolean))],
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
      if (filters.owner && !alert.jsm_owner?.toLowerCase().includes(filters.owner.toLowerCase())) {
        return false;
      }
      if (filters.acknowledgedBy && !alert.acknowledged_by?.toLowerCase().includes(filters.acknowledgedBy.toLowerCase())) {
        return false;
      }
      if (filters.resolvedBy && !alert.resolved_by?.toLowerCase().includes(filters.resolvedBy.toLowerCase())) {
        return false;
      }

      // Array filters
      if (filters.severity.length > 0 && !filters.severity.includes(alert.severity)) {
        return false;
      }
      if (filters.grafanaStatus.length > 0 && !filters.grafanaStatus.includes(alert.grafana_status)) {
        return false;
      }
      if (filters.jsmStatus.length > 0 && !filters.jsmStatus.includes(alert.jsm_status)) {
        return false;
      }
      if (filters.jsmPriority.length > 0 && !filters.jsmPriority.includes(alert.jsm_priority)) {
         return false;
      }
      if (filters.matchType.length > 0 && !filters.matchType.includes(alert.match_type)) {
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

  const updateFilter = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      alertName: '',
      cluster: '',
      severity: [],
      grafanaStatus: [],
      jsmStatus: [],
      jsmPriority: [],
      matchType: [],
      owner: '',
      acknowledgedBy: '',
      resolvedBy: '',
      dateRange: null
    });
    setSelectedRowKeys([]);
  };

  // Logic to check if any selected alerts can be acknowledged
  const { eligibleForAck, eligibleForAckCount } = useMemo(() => {
    if (selectedRowKeys.length === 0) {
      return { eligibleForAck: false, eligibleForAckCount: 0 };
    }
    const eligibleAlerts = selectedRowKeys.filter(key => {
      const alert = alerts.find(a => a.id === key);
      // Can be acknowledged if it has a JSM alert and is not already acked or closed
      return alert && alert.jsm_alert_id && alert.jsm_status !== 'acked' && alert.jsm_status !== 'closed';
    });
    return { eligibleForAck: eligibleAlerts.length > 0, eligibleForAckCount: eligibleAlerts.length };
  }, [selectedRowKeys, alerts]);

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
      acked: 'blue',
      acknowledged: 'blue',
      closed: 'green',
    };
    return colors[status?.toLowerCase()] || 'default';
  };

  const getMatchTypeColor = (matchType) => {
    const colors = {
      high_confidence: 'green',
      content_similarity: 'blue',
      low_confidence: 'orange',
      none: 'default'
    };
    return colors[matchType] || 'default';
  };

  const getMatchTypeIcon = (matchType) => {
    const icons = {
      high_confidence: <CheckCircleOutlined />,
      content_similarity: <ApiOutlined />,
      low_confidence: <WarningOutlined />,
      none: <ExclamationCircleOutlined />
    };
    return icons[matchType] || <QuestionCircleOutlined />;
  };

  const showAlertDetails = (alert) => {
    setSelectedAlert(alert);
    setDetailModalVisible(true);
  };

  const getJSMUrl = (alert) => {
    if (alert.jsm_alert_id) {
      const baseUrl = process.env.REACT_APP_JIRA_URL || 'https://devoinc.atlassian.net';
      // Construct the new, simplified JSM alert URL
      return `${baseUrl}/jira/ops/alerts/${alert.jsm_alert_id}`;
    }
    return null;
  };

  const columns = [
    {
      title: 'Alert Name',
      dataIndex: 'alert_name',
      key: 'alert_name',
      sorter: (a, b) => (a.alert_name || '').localeCompare(b.alert_name || ''),
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>
            <Button 
              type="link" 
              onClick={() => showAlertDetails(record)}
              style={{ padding: 0, height: 'auto', fontWeight: 'bold' }}
            >
              {text}
            </Button>
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {record.cluster && `Cluster: ${record.cluster}`}
            {record.pod && ` | Pod: ${record.pod}`}
          </div>
        </div>
      ),
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      sorter: (a, b) => {
        const severityOrder = { critical: 4, warning: 3, info: 2, unknown: 1 };
        return (severityOrder[a.severity] || 0) - (severityOrder[b.severity] || 0);
      },
      render: (severity) => (
        <Tag color={getSeverityColor(severity)}>
          {severity?.toUpperCase() || 'UNKNOWN'}
        </Tag>
      ),
    },
    {
      title: 'Grafana Status',
      dataIndex: 'grafana_status',
      key: 'grafana_status',
      sorter: (a, b) => (a.grafana_status || '').localeCompare(b.grafana_status || ''),
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {status?.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'JSM Status & Match',
      key: 'jsm_info',
      sorter: (a, b) => (a.jsm_status || 'none').localeCompare(b.jsm_status || 'none'),
      render: (_, record) => (
        <div>
          <div style={{ marginBottom: '4px' }}>
            {record.jsm_status ? (
              <Space>
                <Tag color={getStatusColor(record.jsm_status)}>
                  JSM: {record.jsm_status?.toUpperCase()}
                </Tag>
                {record.jsm_acknowledged && (
                  <Tag color="blue" size="small">
                    ACK
                  </Tag>
                )}
              </Space>
            ) : (
              <Tag color="default">No JSM Alert</Tag>
            )}
          </div>
          <div>
            <Tag 
              color={getMatchTypeColor(record.match_type)} 
              size="small"
              icon={getMatchTypeIcon(record.match_type)}
            >
              {record.match_type || 'none'}: {record.match_confidence || 0}%
            </Tag>
          </div>
        </div>
      ),
    },
    {
      title: 'Owner / Acknowledged By',
      key: 'assignee_info',
      sorter: (a, b) => {
        const aName = a.jsm_owner || a.acknowledged_by || '';
        const bName = b.jsm_owner || b.acknowledged_by || '';
        return aName.localeCompare(bName);
      },
      render: (_, record) => (
        <div>
          {record.jsm_owner && (
            <div style={{ marginBottom: '4px' }}>
              <Avatar size="small" icon={<UserOutlined />} style={{ marginRight: '4px' }} />
              <Tooltip title={`JSM Owner: ${record.jsm_owner}`}>
                <span style={{ fontSize: '12px', color: '#1890ff' }}>
                  {record.jsm_owner}
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
          {!record.jsm_owner && !record.acknowledged_by && !record.resolved_by && (
            <span style={{ color: '#ccc', fontSize: '12px' }}>Unassigned</span>
          )}
        </div>
      ),
    },
    {
        title: 'Alert Details',
        key: 'links_actions',
        render: (_, record) => {
            const jsmUrl = getJSMUrl(record);
            const grafanaUrl = record.generator_url;

            return (
                <Space direction="vertical" align="start" size={4}>
                    {grafanaUrl && (
                        <a href={grafanaUrl} target="_blank" rel="noopener noreferrer" style={{ display: 'flex', alignItems: 'center' }}>
                            <LinkOutlined style={{ marginRight: 5 }} /> View in Grafana
                        </a>
                    )}
                    {jsmUrl && (
                        <a href={jsmUrl} target="_blank" rel="noopener noreferrer" style={{ display: 'flex', alignItems: 'center' }}>
                            <ThunderboltOutlined style={{ marginRight: 5 }} /> View in JSM
                        </a>
                    )}
                    <Button
                        type="link"
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={() => showAlertDetails(record)}
                        style={{ padding: 0, height: 'auto', display: 'flex', alignItems: 'center' }}
                    >
                        <EyeOutlined style={{ marginRight: 5 }} /> Show Details
                    </Button>
                </Space>
            );
        },
    },
    {
      title: 'Created / Updated',
      key: 'timestamps',
      sorter: (a, b) => {
        const dateA = moment(a.created_at);
        const dateB = moment(b.created_at);
        return dateA.isBefore(dateB) ? -1 : dateA.isAfter(dateB) ? 1 : 0;
      },
      defaultSortOrder: 'descend',
      render: (_, record) => (
        <div>
          <div style={{ fontSize: '12px' }}>
            <strong>Created:</strong> {moment(record.created_at).format('MM/DD HH:mm')}
          </div>
          {record.started_at && (
            <div style={{ fontSize: '10px', color: '#666' }}>
              Started: {moment(record.started_at).format('MM/DD HH:mm')}
            </div>
          )}
          {record.jsm_created_at && (
            <div style={{ fontSize: '10px', color: '#1890ff' }}>
              JSM: {moment(record.jsm_created_at).format('MM/DD HH:mm')}
            </div>
          )}
        </div>
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
        message.success(`Successfully acknowledged ${selectedRowKeys.length} alert${selectedRowKeys.length > 1 ? 's' : ''} in JSM`);
        setSelectedRowKeys([]);
        setAcknowledgeModalVisible(false);
        acknowledgeForm.resetFields();
      } else {
        message.error('Failed to acknowledge alerts in JSM');
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
        message.success(`Successfully resolved ${selectedRowKeys.length} alert${selectedRowKeys.length > 1 ? 's' : ''} in JSM`);
        setSelectedRowKeys([]);
        setResolveModalVisible(false);
        resolveForm.resetFields();
      } else {
        message.error('Failed to resolve alerts in JSM');
      }
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  // Calculate statistics
  const stats = useMemo(() => {
    const matched = filteredAlerts.filter(a => a.jsm_alert_id).length;
    const unmatched = filteredAlerts.length - matched;
    const acknowledged = filteredAlerts.filter(a => a.jsm_acknowledged || a.acknowledged_by).length;
    const resolved = filteredAlerts.filter(a => a.grafana_status === 'resolved').length;
    const critical = filteredAlerts.filter(a => a.severity === 'critical' && a.grafana_status === 'active').length;
    const matchRate = filteredAlerts.length > 0 ? Math.round((matched / filteredAlerts.length) * 100) : 0;
    
    return { matched, unmatched, acknowledged, resolved, critical, total: filteredAlerts.length, matchRate };
  }, [filteredAlerts]);

  return (
    <div>
      {/* Status Summary Card */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col xs={24} sm={12} md={16} lg={18}>
            <Space wrap>
              <Badge count={stats.total} showZero color="#1890ff">
                <Tag>Total Alerts</Tag>
              </Badge>
              <Badge count={stats.matched} showZero color="#52c41a">
                <Tag>JSM Matched</Tag>
              </Badge>
              <Badge count={stats.unmatched} showZero color="#fa8c16">
                <Tag>Unmatched</Tag>
              </Badge>
              <Badge count={stats.acknowledged} showZero color="#1890ff">
                <Tag>Acknowledged</Tag>
              </Badge>
              <Badge count={stats.critical} showZero color="#ff4d4f">
                <Tag>Critical</Tag>
              </Badge>
              {selectedRowKeys.length > 0 && (
                <Badge count={selectedRowKeys.length} showZero color="#722ed1">
                  <Tag>Selected</Tag>
                </Badge>
              )}
            </Space>
          </Col>
          <Col xs={24} sm={12} md={8} lg={6} style={{ textAlign: 'right' }}>
            <Space>
              <Button
                icon={<SyncOutlined />}
                onClick={onSync}
                loading={loading}
                type="primary"
              >
                Sync with JSM
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Filter Panel */}
      <Card 
        title={
          <Space>
            <FilterOutlined />
            Filters & Search
            <Tag color={filteredAlerts.length !== alerts.length ? 'blue' : 'default'}>
              {filteredAlerts.length} of {alerts.length} alerts
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
              onClick={clearFilters}
            >
              Clear Filters
            </Button>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
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
              placeholder="Filter by JSM status"
              value={filters.jsmStatus}
              onChange={(value) => updateFilter('jsmStatus', value)}
              style={{ width: '100%' }}
              allowClear
            >
              {uniqueValues.jsmStatuses.map(status => (
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
              placeholder="Filter by match type"
              value={filters.matchType}
              onChange={(value) => updateFilter('matchType', value)}
              style={{ width: '100%' }}
              allowClear
            >
              {uniqueValues.matchTypes.map(type => (
                <Option key={type} value={type}>
                  <Tag color={getMatchTypeColor(type)} size="small" icon={getMatchTypeIcon(type)}>
                    {type}
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
                  placeholder="Search JSM owner..."
                  prefix={<UserOutlined />}
                  value={filters.owner}
                  onChange={(e) => updateFilter('owner', e.target.value)}
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
            disabled={!eligibleForAck}
          >
            Acknowledge in JSM ({eligibleForAckCount})
          </Button>
          
          <Button
            type="primary"
            danger
            icon={<CloseOutlined />}
            onClick={() => setResolveModalVisible(true)}
            disabled={selectedRowKeys.length === 0}
          >
            Close in JSM ({selectedRowKeys.length})
          </Button>

          <Button
            onClick={() => setSelectedRowKeys([])}
            disabled={selectedRowKeys.length === 0}
          >
            Clear Selection
          </Button>
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
            disabled: record.grafana_status === 'resolved',
          }),
        }}
        loading={loading}
        pagination={{
          position: ['topRight'],
          pageSize: 50,
          showSizeChanger: true,
          pageSizeOptions: ['10', '25', '50', '100', '200'],
          showQuickJumper: true,
          showTotal: (total, range) => 
            `${range[0]}-${range[1]} of ${total} alerts${filteredAlerts.length !== alerts.length ? ` (filtered from ${alerts.length})` : ''}`,
        }}
        scroll={{ x: 1800 }}
        size="small"
      />

      {/* Alert Details Modal */}
      <Modal
        title={
          <Space>
            <InfoCircleOutlined />
            {'Alert Details  '}
            {selectedAlert?.jsm_alert_id && (
              <Tag color="blue">JSM Alert</Tag>
            )}
            {selectedAlert?.match_type && selectedAlert.match_type !== 'none' && (
              <Tag color={getMatchTypeColor(selectedAlert.match_type)}>
                {selectedAlert.match_confidence}% match
              </Tag>
            )}
          </Space>
        }
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        width={800}
        footer={
          <Space>
            <Button onClick={() => setDetailModalVisible(false)}>
              Close
            </Button>
            {selectedAlert?.generator_url && (
              <Button 
                type="primary"
                onClick={() => window.open(selectedAlert.generator_url, '_blank')}
              >
                View in Grafana
              </Button>
            )}
            {selectedAlert?.jsm_alert_id && getJSMUrl(selectedAlert) && (
              <Button 
                type="primary"
                icon={<ThunderboltOutlined />}
                onClick={() => window.open(getJSMUrl(selectedAlert), '_blank')}
              >
                View in JSM
              </Button>
            )}
          </Space>
        }
      >
        {selectedAlert && (
          <div>
            {/* Basic Alert Info */}
            <Card size="small" title="Alert Information" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={12}>
                  <div><strong>Name:</strong> {selectedAlert.alert_name}</div>
                  <div><strong>Cluster:</strong> {selectedAlert.cluster || 'N/A'}</div>
                  <div><strong>Pod:</strong> {selectedAlert.pod || 'N/A'}</div>
                  <div><strong>Severity:</strong> <Tag color={getSeverityColor(selectedAlert.severity)}>{selectedAlert.severity}</Tag></div>
                </Col>
                <Col span={12}>
                  <div><strong>Grafana Status:</strong> <Tag color={getStatusColor(selectedAlert.grafana_status)}>{selectedAlert.grafana_status}</Tag></div>
                  <div><strong>Started:</strong> {selectedAlert.started_at ? moment(selectedAlert.started_at).format('YYYY-MM-DD HH:mm:ss') : 'N/A'}</div>
                  <div><strong>Created:</strong> {moment(selectedAlert.created_at).format('YYYY-MM-DD HH:mm:ss')}</div>
                </Col>
              </Row>
              {selectedAlert.summary && (
                <div style={{ marginTop: 12 }}>
                  <strong>Summary:</strong>
                  <div style={{ marginTop: 4, padding: 8, background: '#f6f8fa', borderRadius: 4 }}>
                    {selectedAlert.summary}
                  </div>
                </div>
              )}
            </Card>

            {/* JSM Information */}
            {selectedAlert.jsm_alert_id ? (
              <Card size="small" title="JSM Alert Information" style={{ marginBottom: 16 }}>
                <Row gutter={16}>
                  <Col span={12}>
                    <div><strong>JSM Alert ID:</strong> {selectedAlert.jsm_tiny_id || selectedAlert.jsm_alert_id}</div>
                    <div><strong>JSM Status:</strong> <Tag color={getStatusColor(selectedAlert.jsm_status)}>{selectedAlert.jsm_status}</Tag></div>
                    <div><strong>Priority:</strong> {selectedAlert.jsm_priority || 'N/A'}</div>
                    <div><strong>Owner:</strong> {selectedAlert.jsm_owner || 'Unassigned'}</div>
                  </Col>
                  <Col span={12}>
                    <div><strong>Acknowledged:</strong> {selectedAlert.jsm_acknowledged ? 'Yes' : 'No'}</div>
                    <div><strong>Source:</strong> {selectedAlert.jsm_source || 'N/A'}</div>
                    <div><strong>Count:</strong> {selectedAlert.jsm_count || 1}</div>
                    <div><strong>Integration:</strong> {selectedAlert.jsm_integration_name || 'N/A'}</div>
                  </Col>
                </Row>
                <div style={{ marginTop: 12 }}>
                  <strong>Match Information:</strong>
                  <div style={{ marginTop: 4 }}>
                    <Tag color={getMatchTypeColor(selectedAlert.match_type)} icon={getMatchTypeIcon(selectedAlert.match_type)}>
                      Type: {selectedAlert.match_type}
                    </Tag>
                    <Tag color="blue">
                      Confidence: {selectedAlert.match_confidence}%
                    </Tag>
                  </div>
                </div>
                {selectedAlert.jsm_tags && selectedAlert.jsm_tags.length > 0 && (
                  <div style={{ marginTop: 12 }}>
                    <strong>JSM Tags:</strong>
                    <div style={{ marginTop: 4 }}>
                      {selectedAlert.jsm_tags.slice(0, 10).map((tag, index) => (
                        <Tag key={index} size="small" style={{ margin: '2px' }}>
                          {tag}
                        </Tag>
                      ))}
                      {selectedAlert.jsm_tags.length > 10 && (
                        <Tag size="small">+{selectedAlert.jsm_tags.length - 10} more</Tag>
                      )}
                    </div>
                  </div>
                )}
              </Card>
            ) : (
              <Card size="small" title="JSM Matching" style={{ marginBottom: 16 }}>
                <div style={{ textAlign: 'center', padding: 20, color: '#999' }}>
                  <ExclamationCircleOutlined style={{ fontSize: 24, marginBottom: 8 }} />
                  <div>No matching JSM alert found</div>
                  <div style={{ fontSize: '12px' }}>
                    This alert exists only in Grafana or the matching confidence was below the threshold ({selectedAlert.match_confidence || 0}%)
                  </div>
                </div>
              </Card>
            )}

            {/* Actions Taken */}
            {(selectedAlert.acknowledged_by || selectedAlert.resolved_by) && (
              <Card size="small" title="Actions Taken">
                {selectedAlert.acknowledged_by && (
                  <div>
                    <CheckOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                    <strong>Acknowledged by:</strong> {selectedAlert.acknowledged_by}
                    {selectedAlert.acknowledged_at && (
                      <span style={{ marginLeft: 8, color: '#666' }}>
                        on {moment(selectedAlert.acknowledged_at).format('YYYY-MM-DD HH:mm:ss')}
                      </span>
                    )}
                  </div>
                )}
                {selectedAlert.resolved_by && (
                  <div style={{ marginTop: 8 }}>
                    <CloseOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                    <strong>Resolved by:</strong> {selectedAlert.resolved_by}
                    {selectedAlert.resolved_at && (
                      <span style={{ marginLeft: 8, color: '#666' }}>
                        on {moment(selectedAlert.resolved_at).format('YYYY-MM-DD HH:mm:ss')}
                      </span>
                    )}
                  </div>
                )}
              </Card>
            )}
          </div>
        )}
      </Modal>

      {/* Acknowledge Modal */}
      <Modal
        title="Acknowledge Alerts in JSM"
        open={acknowledgeModalVisible}
        onOk={handleAcknowledge}
        onCancel={() => {
          setAcknowledgeModalVisible(false);
          acknowledgeForm.resetFields();
        }}
        okText="Acknowledge in JSM"
      >
        <p>Are you sure you want to acknowledge {selectedRowKeys.length} alert(s) in JSM?</p>
        <p>This will transition the JSM alerts to acknowledged status.</p>
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

      {/* Resolve Modal */}
      <Modal
        title="Close Alerts in JSM"
        open={resolveModalVisible}
        onOk={handleResolve}
        onCancel={() => {
          setResolveModalVisible(false);
          resolveForm.resetFields();
        }}
        okText="Close in JSM"
        okButtonProps={{ danger: true }}
      >
        <p>Are you sure you want to close {selectedRowKeys.length} alert(s) in JSM?</p>
        <p>This will close the JSM alerts and mark them as resolved in the system.</p>.
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