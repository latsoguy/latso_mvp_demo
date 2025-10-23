import React from 'react';
import { AlertCircle, CheckCircle, Clock, TrendingUp } from 'lucide-react';

interface DataSource {
  name: string;
  confidence: number;
  lastSync: string;
  status: 'good' | 'stale' | 'missing';
  improvementActions: string[];
}

const DataQualityPanel: React.FC = () => {
  const dataSources: DataSource[] = [
    {
      name: 'Schedule Data',
      confidence: 95,
      lastSync: 'Daily sync (2 hours ago)',
      status: 'good',
      improvementActions: []
    },
    {
      name: 'Vendor Data', 
      confidence: 60,
      lastSync: '18 days stale',
      status: 'stale',
      improvementActions: [
        'Upload contract amendment → +15% confidence',
        'Sync vendor tracker → +8% confidence'
      ]
    },
    {
      name: 'Cost Data',
      confidence: 85,
      lastSync: 'ERP integrated (1 hour ago)',
      status: 'good',
      improvementActions: []
    },
    {
      name: 'Contract Data',
      confidence: 50,
      lastSync: 'Outdated version (45 days)',
      status: 'stale',
      improvementActions: [
        'Upload latest contract amendments → +25% confidence',
        'Update penalty clauses → +10% confidence'
      ]
    }
  ];

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-600 bg-green-50 border-green-200';
    if (confidence >= 60) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'good': return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'stale': return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'missing': return <AlertCircle className="w-5 h-5 text-red-500" />;
      default: return <AlertCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  const overallConfidence = Math.round(
    dataSources.reduce((sum, source) => sum + source.confidence, 0) / dataSources.length
  );

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <TrendingUp className="w-6 h-6 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Data Quality & Trust Score</h3>
        </div>
        <div className={`px-4 py-2 rounded-full border ${getConfidenceColor(overallConfidence)}`}>
          <span className="font-semibold">{overallConfidence}% Overall Confidence</span>
        </div>
      </div>

      <div className="space-y-4">
        {dataSources.map((source, idx) => (
          <div key={idx} className="border border-gray-200 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                {getStatusIcon(source.status)}
                <div>
                  <h4 className="font-medium text-gray-900">{source.name}</h4>
                  <p className="text-sm text-gray-500">{source.lastSync}</p>
                </div>
              </div>
              <div className={`px-3 py-1 rounded-full border ${getConfidenceColor(source.confidence)}`}>
                <span className="font-medium">{source.confidence}%</span>
              </div>
            </div>

            {source.improvementActions.length > 0 && (
              <div className="mt-3 space-y-2">
                <p className="text-sm font-medium text-gray-700">How to improve:</p>
                {source.improvementActions.map((action, actionIdx) => (
                  <div key={actionIdx} className="flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-700 cursor-pointer">
                    <span>→</span>
                    <span>{action}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-blue-50 rounded-xl">
        <p className="text-blue-800 text-sm">
          <strong>Pro Tip:</strong> Addressing vendor data staleness could improve your risk predictions by 15-20%.
          Upload recent contract amendments to boost confidence immediately.
        </p>
      </div>
    </div>
  );
};

export default DataQualityPanel;