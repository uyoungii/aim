from fastapi import Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

from aim.web.api.runs.audio_utils import (
    requested_audio_traces_streamer,
    audio_search_result_streamer,
    audios_batch_result_streamer
)
from aim.web.api.utils import APIRouter  # wrapper for fastapi.APIRouter
from typing import Optional, Tuple

from aim.web.api.projects.project import Project
from aim.web.api.runs.utils import (
    collect_requested_metric_traces,
    requested_distribution_traces_streamer,
    requested_text_traces_streamer,
    custom_aligned_metrics_streamer,
    get_run_props,
    metric_search_result_streamer,
    run_search_result_streamer,
    str_to_range,
)
from aim.web.api.runs.image_utils import (
    requested_image_traces_streamer,
    image_search_result_streamer,
    images_batch_result_streamer,
)
from aim.web.api.runs.pydantic_models import (
    MetricAlignApiIn,
    QuerySyntaxErrorOut,
    RunTracesBatchApiIn,
    RunMetricCustomAlignApiOut,
    RunMetricSearchApiOut,
    RunImagesSearchApiOut,
    RunAudiosSearchApiOut,
    RunFiguresSearchApiOut,
    RunInfoOut,
    RunsBatchIn,
    RunSearchApiOut,
    RunMetricsBatchApiOut,
    RunImagesBatchApiOut,
    RunAudiosBatchApiOut,
    RunFiguresBatchApiOut,
    RunDistributionsBatchApiOut,
    RunTextsBatchApiOut,
    StructuredRunUpdateIn,
    StructuredRunUpdateOut,
    StructuredRunAddTagIn,
    StructuredRunAddTagOut,
    StructuredRunRemoveTagOut,
    StructuredRunsArchivedOut,
    URIBatchIn,
)
from aim.web.api.utils import object_factory
from aim.storage.query import syntax_error_check
from aim.web.api.runs.figure_utils import (
    requested_figure_object_traces_streamer,
    figure_batch_result_streamer,
    figure_search_result_streamer
)

runs_router = APIRouter()


@runs_router.get('/search/run/', response_model=RunSearchApiOut,
                 responses={400: {'model': QuerySyntaxErrorOut}})
def run_search_api(q: Optional[str] = '', limit: Optional[int] = 0, offset: Optional[str] = None):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)

    query = q.strip()
    try:
        syntax_error_check(query)
    except SyntaxError as se:
        raise HTTPException(status_code=400, detail={
            'name': 'SyntaxError',
            'statement': se.text,
            'line': se.lineno,
            'offset': se.offset
        })
    runs = project.repo.query_runs(query=query, paginated=bool(limit), offset=offset)

    streamer = run_search_result_streamer(runs, limit)
    return StreamingResponse(streamer)


@runs_router.post('/search/metric/align/', response_model=RunMetricCustomAlignApiOut)
def run_metric_custom_align_api(request_data: MetricAlignApiIn):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)

    x_axis_metric_name = request_data.align_by
    requested_runs = request_data.runs

    streamer = custom_aligned_metrics_streamer(requested_runs, x_axis_metric_name, project.repo)
    return StreamingResponse(streamer)


@runs_router.get('/search/metric/', response_model=RunMetricSearchApiOut,
                 responses={400: {'model': QuerySyntaxErrorOut}})
async def run_metric_search_api(q: Optional[str] = '',
                                p: Optional[int] = 50,
                                x_axis: Optional[str] = None):
    steps_num = p

    if x_axis:
        x_axis = x_axis.strip()

    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)

    query = q.strip()
    try:
        syntax_error_check(query)
    except SyntaxError as se:
        raise HTTPException(status_code=400, detail={
            'name': 'SyntaxError',
            'statement': se.text,
            'line': se.lineno,
            'offset': se.offset
        })

    traces = project.repo.query_metrics(query=query)

    streamer = metric_search_result_streamer(traces, steps_num, x_axis)
    return StreamingResponse(streamer)


@runs_router.get('/search/images/', response_model=RunImagesSearchApiOut,
                 responses={400: {'model': QuerySyntaxErrorOut}})
async def run_images_search_api(q: Optional[str] = '',
                                record_range: Optional[str] = '', record_density: Optional[int] = 50,
                                index_range: Optional[str] = '', index_density: Optional[int] = 5,
                                calc_ranges: Optional[bool] = False):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)

    query = q.strip()
    try:
        syntax_error_check(query)
    except SyntaxError as se:
        raise HTTPException(status_code=400, detail={
            'name': 'SyntaxError',
            'statement': se.text,
            'line': se.lineno,
            'offset': se.offset
        })

    traces = project.repo.query_images(query=query)

    try:
        record_range = str_to_range(record_range)
        index_range = str_to_range(index_range)
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid range format')

    streamer = image_search_result_streamer(traces, record_range, record_density,
                                            index_range, index_density, calc_ranges)
    return StreamingResponse(streamer)


@runs_router.get('/search/audios/', response_model=RunAudiosSearchApiOut,
                 responses={400: {'model': QuerySyntaxErrorOut}})
async def run_audios_search_api(q: Optional[str] = '',
                                record_range: Optional[str] = '', record_density: Optional[int] = 50,
                                index_range: Optional[str] = '', index_density: Optional[int] = 5,
                                calc_ranges: Optional[bool] = False):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)

    query = q.strip()
    try:
        syntax_error_check(query)
    except SyntaxError as se:
        raise HTTPException(status_code=400, detail={
            'name': 'SyntaxError',
            'statement': se.text,
            'line': se.lineno,
            'offset': se.offset
        })

    traces = project.repo.query_audios(query=query)

    try:
        record_range = str_to_range(record_range)
        index_range = str_to_range(index_range)
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid range format')

    streamer = audio_search_result_streamer(traces, record_range, record_density,
                                            index_range, index_density, calc_ranges)
    return StreamingResponse(streamer)


@runs_router.get('/search/figures/', response_model=RunFiguresSearchApiOut,
                 responses={400: {'model': QuerySyntaxErrorOut}})
async def run_figures_search_api(q: Optional[str] = '',
                                 record_range: Optional[str] = '',
                                 record_density: Optional[int] = 50,
                                 calc_ranges: Optional[bool] = False):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)

    query = q.strip()
    try:
        syntax_error_check(query)
    except SyntaxError as se:
        raise HTTPException(status_code=400, detail={
            'name': 'SyntaxError',
            'statement': se.text,
            'line': se.lineno,
            'offset': se.offset
        })

    traces = project.repo.query_figure_objects(query=query)

    try:
        record_range = str_to_range(record_range)
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid range format')

    streamer = figure_search_result_streamer(traces, record_range, record_density, calc_ranges)
    return StreamingResponse(streamer)


@runs_router.post('/images/get-batch/')
def image_blobs_batch_api(uri_batch: URIBatchIn):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)

    return StreamingResponse(images_batch_result_streamer(uri_batch, project.repo))


@runs_router.post('/audios/get-batch/')
def audio_blobs_batch_api(uri_batch: URIBatchIn):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)

    return StreamingResponse(audios_batch_result_streamer(uri_batch, project.repo))


@runs_router.post('/figures/get-batch/')
def figure_blobs_batch_api(uri_batch: URIBatchIn):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)

    return StreamingResponse(figure_batch_result_streamer(uri_batch, project.repo))


@runs_router.get('/{run_id}/info/', response_model=RunInfoOut)
async def run_params_api(run_id: str, sequence: Optional[Tuple[str, ...]] = Query(())):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)
    run = project.repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404)

    if sequence != ():
        try:
            project.repo.validate_sequence_types(sequence)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        sequence = project.repo.available_sequence_types()

    response = {
        'params': run.get(...),
        'traces': run.collect_sequence_info(sequence, skip_last_value=True),
        'props': get_run_props(run)
    }
    return JSONResponse(response)


@runs_router.post('/{run_id}/metric/get-batch/', response_model=RunMetricsBatchApiOut)
async def run_metric_batch_api(run_id: str, requested_traces: RunTracesBatchApiIn):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)
    run = project.repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404)

    traces_data = collect_requested_metric_traces(run, requested_traces)

    return JSONResponse(traces_data)


@runs_router.post('/{run_id}/images/get-batch/', response_model=RunImagesBatchApiOut)
async def run_images_batch_api(run_id: str,
                               requested_traces: RunTracesBatchApiIn,
                               record_range: Optional[str] = '', record_density: Optional[int] = 50,
                               index_range: Optional[str] = '', index_density: Optional[int] = 5):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)
    run = project.repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404)

    try:
        record_range = str_to_range(record_range)
        index_range = str_to_range(index_range)
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid range format')

    traces_streamer = requested_image_traces_streamer(run, requested_traces,
                                                      record_range, index_range,
                                                      record_density, index_density)

    return StreamingResponse(traces_streamer)


@runs_router.post('/{run_id}/audios/get-batch/', response_model=RunAudiosBatchApiOut)
async def run_audios_batch_api(run_id: str,
                               requested_traces: RunTracesBatchApiIn,
                               record_range: Optional[str] = '', record_density: Optional[int] = 50,
                               index_range: Optional[str] = '', index_density: Optional[int] = 5):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)
    run = project.repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404)

    try:
        record_range = str_to_range(record_range)
        index_range = str_to_range(index_range)
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid range format')

    traces_streamer = requested_audio_traces_streamer(run, requested_traces,
                                                      record_range, index_range,
                                                      record_density, index_density)

    return StreamingResponse(traces_streamer)


@runs_router.post('/{run_id}/figures/get-batch/', response_model=RunFiguresBatchApiOut)
async def run_figures_batch_api(run_id: str,
                                requested_traces: RunTracesBatchApiIn,
                                record_range: Optional[str] = '',
                                record_density: Optional[int] = 50):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)
    run = project.repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404)  # Get project

    try:
        record_range = str_to_range(record_range)
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid range format')

    traces_streamer = requested_figure_object_traces_streamer(run,
                                                              requested_traces,
                                                              record_range,
                                                              record_density)

    return StreamingResponse(traces_streamer)


@runs_router.post('/{run_id}/distributions/get-batch/', response_model=RunDistributionsBatchApiOut)
async def run_distributions_batch_api(run_id: str,
                                      requested_traces: RunTracesBatchApiIn,
                                      record_range: Optional[str] = '',
                                      record_density: Optional[int] = 50):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)
    run = project.repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404)
    try:
        record_range = str_to_range(record_range)
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid range format')

    traces_streamer = requested_distribution_traces_streamer(run, requested_traces, record_range, record_density)

    return StreamingResponse(traces_streamer)


@runs_router.post('/{run_id}/texts/get-batch/', response_model=RunTextsBatchApiOut)
async def run_texts_batch_api(run_id: str,
                              requested_traces: RunTracesBatchApiIn,
                              record_range: Optional[str] = '', record_density: Optional[int] = 50,
                              index_range: Optional[str] = '', index_density: Optional[int] = 5):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)
    run = project.repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404)

    try:
        record_range = str_to_range(record_range)
        index_range = str_to_range(index_range)
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid range format')

    traces_streamer = requested_text_traces_streamer(run, requested_traces,
                                                     record_range, index_range,
                                                     record_density, index_density)

    return StreamingResponse(traces_streamer)


@runs_router.put('/{run_id}/', response_model=StructuredRunUpdateOut)
async def update_run_properties_api(run_id: str, run_in: StructuredRunUpdateIn, factory=Depends(object_factory)):
    with factory:
        run = factory.find_run(run_id)
        if not run:
            raise HTTPException(status_code=404)

        if run_in.name:
            run.name = run_in.name.strip()
        if run_in.description:
            run.description = run_in.description.strip()
        if run_in.experiment:
            run.experiment = run_in.experiment.strip()
        run.archived = run_in.archived

    return {
        'id': run.hash,
        'status': 'OK'
    }


@runs_router.post('/{run_id}/tags/new/', response_model=StructuredRunAddTagOut)
async def add_run_tag_api(run_id: str, tag_in: StructuredRunAddTagIn, factory=Depends(object_factory)):
    with factory:
        run = factory.find_run(run_id)
        if not run:
            raise HTTPException(status_code=404)

        run.add_tag(tag_in.tag_name)
        tag = next(iter(factory.search_tags(tag_in.tag_name)))
    return {
        'id': run.hash,
        'tag_id': tag.uuid,
        'status': 'OK'
    }


@runs_router.delete('/{run_id}/tags/{tag_id}/', response_model=StructuredRunRemoveTagOut)
async def remove_run_tag_api(run_id: str, tag_id: str, factory=Depends(object_factory)):
    with factory:
        run = factory.find_run(run_id)
        tag = factory.find_tag(tag_id)
        if not (run or tag):
            raise HTTPException(status_code=404)

        removed = run.remove_tag(tag.name)

    return {
        'id': run.hash,
        'removed': removed,
        'status': 'OK'
    }


@runs_router.delete('/{run_id}/')
async def delete_run_api(run_id: str):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)
    success = project.repo.delete_run(run_id)
    if not success:
        raise HTTPException(400, detail=f'Error while deleting run {run_id}.')

    return {
        'id': run_id,
        'status': 'OK'
    }


@runs_router.post('/delete-batch/')
async def delete_runs_batch_api(runs_batch: RunsBatchIn):
    # Get project
    project = Project()
    if not project.exists():
        raise HTTPException(status_code=404)
    success, remaining_runs = project.repo.delete_runs(runs_batch)
    if not success:
        raise HTTPException(400, detail={'message': 'Error while deleting runs.',
                                         'remaining_runs': remaining_runs})

    return {
        'status': 'OK'
    }


@runs_router.post('/archive-batch/', response_model=StructuredRunsArchivedOut)
async def archive_runs_batch_api(runs_batch: RunsBatchIn, archive: Optional[bool] = True,
                                 factory=Depends(object_factory)):
    with factory:
        runs = factory.find_runs(runs_batch)
        if not runs:
            raise HTTPException(status_code=404)

        for run in runs:
            run.archived = archive

    return {
        'status': 'OK'
    }
