import { IChartTitle } from 'types/services/models/metrics/metricsAppModel';
import { ITrendlineOptions } from 'types/services/models/scatter/scatterAppModel';
import { ISyncHoverStateArgs } from 'types/utils/d3/drawHoverAttributes';
import { IDimensionType } from 'types/utils/d3/drawParallelAxes';

export interface IPoint {
  key: string;
  data: {
    xValues: number[] | string[];
    yValues: number[] | string[];
  };
  color: string;
  groupKey: string;
  chartIndex?: number;
}

export interface IScatterPlotProps {
  index: number;
  data: { dimensions: IDimensionType[]; data: IPoint[] };
  chartTitle?: IChartTitle;
  trendlineOptions: ITrendlineOptions;
  syncHoverState: (args: ISyncHoverStateArgs) => void;
}
