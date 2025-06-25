import React, { useState, useEffect } from 'react';
import {
  Modal,
  Form,
  Select,
  DatePicker,
  Button,
  Space,
  Card,
  Statistic,
  Row,
  Col,
  Divider,
  Switch,
  Alert,
  Progress,
  message,
  Typography,
  Tag,
  Tooltip
} from 'antd';
import {
  DownloadOutlined,
  InfoCircleOutlined,
  FilterOutlined,
  FileExcelOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import moment from 'moment';
import axios from 'axios';

const { Option } = Select;
const { RangePicker } = DatePicker;
const { Text, Title } = Typography;

const CSVExportModal = ({ visible, onCancel, alerts = [] }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [summary, setSummary] = useState(null);
  const [previewData, setPreviewData] = useState(null);

  // Fetch export summary on mount
  useEffect(() => {
    if (visible) {
      fetchExportSummary();
      // Set default form values
      form.setFieldsValue({
        include_resolved: true,
        format: 'csv'
      });
    }
  }, [visible]);

  const fetchExportSummary = async () => {
    try {
      const response = await axios.get('/api/alerts/export/summary');
      setSummary(response.data);
    } catch (error) {
      console.error('Failed to fetch export summary:', error);
      message.error('Failed to load export summary');
    }
  };

  const handleExport = async () => {
    try {
      setLoading(true);
      setExportProgress(0);
      
      const values = await form.validateFields();
      
      // Build query parameters
      const params = new URLSearchParams();
      
      if (values.severity && values.severity.length > 0) {
        values.severity.forEach(s => params.append('severity', s));
      }
      if (values.grafana_status && values.grafana_status.length > 0) {
        values.grafana_status.forEach(s => params.append('grafana_status', s));
      }
      if (values.jira_status && values.jira_status.length > 0) {
        values.jira_status.forEach(s => params.append('jira_status', s));
      }
      if (values.cluster) {
        params.append('cluster', values.cluster);
      }
      if (values.date_range && values.date_range.length === 2) {
        params.append('date_from', values.date_range[0].toISOString());
        params.append('date_to', values.date_range[1].toISOString());
      }
      params.append('include_resolved', values.include_resolved);

      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setExportProgress(prev => Math.min(prev + 20, 80));
      }, 200);

      // Make the export request
      const response = await axios.get(`/api/alerts/export/csv?${params.toString()}`, {
        responseType: 'blob'
      });

      clearInterval(progressInterval);
      setExportProgress(100);

      // Create download link
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Get filename from response headers or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'alerts_export.csv';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=(.+)/);
        if (filenameMatch) {
          filename = filenameMatch[1].replace(/"/g, '');
        }
      }
      
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      message.success(`Export completed! Downloaded ${filename}`);
      
      setTimeout(() => {
        setExportProgress(0);
        onCancel();
      }, 1000);

    } catch (error) {
      console.error('Export failed:', error);
      message.error('Export failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const updatePreview = () => {
    const values = form.getFieldsValue();
    
    // Calculate preview based on current filters
    let filteredCount = alerts.length;
    
    if (values.severity && values.severity.length > 0) {
      filteredCount = alerts.filter(a => values.severity.includes(a.severity)).length;
    }
    if (values.grafana_status && values.grafana_status.length > 0) {
      filteredCount = alerts.filter(a => values.grafana_status.includes(a.grafana_status)).length;
    }
    if (values.jira_status && values.jira_status.length > 0) {
      filteredCount = alerts.filter(a => values.jira_status.includes(a.jira_status)).length;
    }
    if (!values.include_resolved) {
      filteredCount = alerts.filter(a => a.jira_status !== 'resolved').length;
    }

    setPreviewData({
      filtered_count: filteredCount,
      total_count: alerts.length
    });
  };

  // Update preview when form values change
  const handleFormChange = () => {
    updatePreview();
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'red',
      warning: 'orange',
      info: 'blue',
      unknown: 'default'
    };
    return colors[severity] || 'default';
  };

  const getStatusColor = (status) => {
    const colors = {
      open: 'orange',
      acknowledged: 'blue',
      resolved: 'green'
    };
    return colors[status] || 'default';
  };

  return (
    <Modal
      title={
        <Space>
          <FileExcelOutlined />
          Export Alerts to CSV
        </Space>
      }
      open={visible}
      onCancel={onCancel}
      width={800}
      footer={null}
      destroyOnClose
    >
      <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
        {/* Export Summary */}
        {summary && (
          <Card size="small" style={{ marginBottom: 16 }}>
            <Title level={5}>
              <InfoCircleOutlined style={{ marginRight: 8 }} />
              Export Summary
            </Title>
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="Total Alerts"
                  value={summary.total_alerts}
                  prefix={<FilterOutlined />}
                />
              </Col>
              <Col span={6}>
                <div>
                  <Text strong>By Severity</Text>
                  <div style={{ marginTop: 4 }}>
                    {Object.entries(summary.by_severity).map(([severity, count]) => (
                      <Tag key={severity} color={getSeverityColor(severity)} size="small">
                        {severity}: {count}
                      </Tag>
                    ))}
                  </div>
                </div>
              </Col>
              <Col span={6}>
                <div>
                  <Text strong>By Status</Text>
                  <div style={{ marginTop: 4 }}>
                    {Object.entries(summary.by_jira_status).map(([status, count]) => (
                      <Tag key={status} color={getStatusColor(status)} size="small">
                        {status}: {count}
                      </Tag>
                    ))}
                  </div>
                </div>
              </Col>
              <Col span={6}>
                <div>
                  <Text strong>Clusters</Text>
                  <div style={{ marginTop: 4 }}>
                    <Text type="secondary">
                      {Object.keys(summary.by_cluster).length} clusters
                    </Text>
                  </div>
                </div>
              </Col>
            </Row>
          </Card>
        )}

        {/* Export Filters */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <Title level={5}>
            <FilterOutlined style={{ marginRight: 8 }} />
            Export Filters
          </Title>
          
          <Form
            form={form}
            layout="vertical"
            onValuesChange={handleFormChange}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="severity" label="Severity">
                  <Select
                    mode="multiple"
                    placeholder="Select severities to include"
                    allowClear
                  >
                    {summary?.available_filters?.severities?.map(severity => (
                      <Option key={severity} value={severity}>
                        <Tag color={getSeverityColor(severity)} size="small">
                          {severity}
                        </Tag>
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="jira_status" label="Jira Status">
                  <Select
                    mode="multiple"
                    placeholder="Select statuses to include"
                    allowClear
                  >
                    {summary?.available_filters?.statuses?.map(status => (
                      <Option key={status} value={status}>
                        <Tag color={getStatusColor(status)} size="small">
                          {status}
                        </Tag>
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="grafana_status" label="Grafana Status">
                  <Select
                    mode="multiple"
                    placeholder="Select Grafana statuses"
                    allowClear
                  >
                    <Option value="active">
                      <Tag color="orange" size="small">active</Tag>
                    </Option>
                    <Option value="resolved">
                      <Tag color="green" size="small">resolved</Tag>
                    </Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="cluster" label="Cluster">
                  <Select
                    placeholder="Select a cluster"
                    allowClear
                    showSearch
                  >
                    {summary?.available_filters?.clusters?.map(cluster => (
                      <Option key={cluster} value={cluster}>
                        {cluster}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="date_range" label="Date Range">
                  <RangePicker
                    showTime
                    placeholder={['Start date', 'End date']}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="include_resolved" valuePropName="checked" label="Include Options">
                  <div>
                    <Switch
                      checkedChildren="Include Resolved"
                      unCheckedChildren="Exclude Resolved"
                    />
                    <div style={{ marginTop: 4, fontSize: '12px', color: '#666' }}>
                      Include or exclude resolved alerts
                    </div>
                  </div>
                </Form.Item>
              </Col>
            </Row>
          </Form>
        </Card>

        {/* Export Preview */}
        {previewData && (
          <Card size="small" style={{ marginBottom: 16 }}>
            <Title level={5}>
              <ClockCircleOutlined style={{ marginRight: 8 }} />
              Export Preview
            </Title>
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="Alerts to Export"
                  value={previewData.filtered_count}
                  suffix={`/ ${previewData.total_count}`}
                  valueStyle={{ 
                    color: previewData.filtered_count > 0 ? '#3f8600' : '#cf1322' 
                  }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Estimated File Size"
                  value={Math.round((previewData.filtered_count * 0.5))}
                  suffix="KB"
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Export Format"
                  value="CSV"
                  valueStyle={{ color: '#722ed1' }}
                />
              </Col>
            </Row>
            
            {previewData.filtered_count === 0 && (
              <Alert
                message="No alerts match the current filters"
                description="Adjust your filters to include more alerts in the export."
                type="warning"
                showIcon
                style={{ marginTop: 16 }}
              />
            )}
          </Card>
        )}

        {/* Export Progress */}
        {loading && (
          <Card size="small" style={{ marginBottom: 16 }}>
            <div style={{ textAlign: 'center' }}>
              <Progress
                type="circle"
                percent={exportProgress}
                status={exportProgress === 100 ? 'success' : 'active'}
                width={80}
              />
              <div style={{ marginTop: 16 }}>
                <Text>
                  {exportProgress === 100 ? 'Export Complete!' : 'Preparing export...'}
                </Text>
              </div>
            </div>
          </Card>
        )}

        {/* Export Information */}
        <Alert
          message="Export Information"
          description={
            <div>
              <p>The CSV export will include the following columns:</p>
              <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                <li>Alert Details: ID, Name, Cluster, Pod, Severity, Summary, Description</li>
                <li>Status Information: Grafana Status, Jira Status, Issue Key, Assignee</li>
                <li>Tracking Data: Acknowledged By/At, Resolved By/At</li>
                <li>Timestamps: Started At, Created At, Updated At</li>
                <li>Links: Generator URL, Jira Issue URL</li>
              </ul>
            </div>
          }
          type="info"
          icon={<InfoCircleOutlined />}
          style={{ marginBottom: 16 }}
        />
      </div>

      {/* Footer Actions */}
      <div style={{ 
        textAlign: 'right', 
        paddingTop: 16, 
        borderTop: '1px solid #f0f0f0' 
      }}>
        <Space>
          <Button onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
          <Tooltip title={previewData?.filtered_count === 0 ? 'No alerts to export' : ''}>
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={handleExport}
              loading={loading}
              disabled={previewData?.filtered_count === 0}
            >
              Export CSV ({previewData?.filtered_count || 0} alerts)
            </Button>
          </Tooltip>
        </Space>
      </div>
    </Modal>
  );
};

export default CSVExportModal;