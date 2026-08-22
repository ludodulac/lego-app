"""End-to-end M0 pipeline from BuildingModel or ArchitecturalScene to viewer export JSON."""
from __future__ import annotations
import argparse
from pathlib import Path
from brickhouse.building.models import BuildingModel, RoofType
from brickhouse.building.validation import load_building_model
from brickhouse.bricks.assembly import generate_assembly_plan
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, generate_brick_model
from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.export import BrickExportBundle, create_export_bundle, export_bundle_json
from brickhouse.bricks.facade_details import generate_window_surrounds
from brickhouse.bricks.roof import generate_spatial_gable_roof
from brickhouse.bricks.scaling import COURSES_PER_STUD_RATIO
from brickhouse.bricks.scene_architecture import augment_brick_model_with_scene_architecture
from brickhouse.bricks.spatial import generate_spatial_brick_shell
from brickhouse.bricks.windows import generate_window_assemblies
from brickhouse.geometry import generate_building_geometry
from brickhouse.scene.models import ArchitecturalScene
from brickhouse.scene.projection import project_scene_to_building
DEFAULT_FRONT_WIDTH_STUDS=48

def _volume_geometry(geometry,volume_id:str):
    return geometry.model_copy(update={"walls":[w for w in geometry.walls if w.volume_id==volume_id],"roof_planes":[p for p in geometry.roof_planes if p.volume_id==volume_id]})

def _translate_model(model:BrickModel,*,prefix:str,x:int,y:int,z:int):
    return [part.model_copy(update={"placement_id":f"{prefix}:{part.placement_id}","x_studs":part.x_studs+x,"y_studs":part.y_studs+y,"z_plates":part.z_plates+z}) for part in model.parts]

def _single_volume_bundle(building:BuildingModel,geometry,front_width_studs:int)->BrickExportBundle:
    shell=generate_building_brick_shell(geometry,front_width_studs)
    spatial_shell=generate_spatial_brick_shell(shell)
    window_parts,fitted_window_ids=generate_window_assemblies(building,shell)
    facade_details=generate_window_surrounds(building,shell,skip_opening_ids=fitted_window_ids)
    roof=building.roofs[0] if building.roofs else None
    spatial_roof=generate_spatial_gable_roof(geometry,shell) if roof is not None and roof.type is RoofType.GABLE else None
    brick_model=generate_brick_model(spatial_shell,spatial_roof,facade_details,window_parts)
    bom=generate_bom(brick_model); assembly_plan=generate_assembly_plan(brick_model)
    return create_export_bundle(brick_model,bom,assembly_plan,appearance=building.appearance)

def run_m0_pipeline_model(building:BuildingModel,*,front_width_studs:int=DEFAULT_FRONT_WIDTH_STUDS)->BrickExportBundle:
    """Run M0 on one or more rectangular volumes using one shared global scale."""
    if front_width_studs<=0: raise ValueError("front_width_studs must be positive")
    geometry=generate_building_geometry(building)
    if len(building.volumes)==1:
        return _single_volume_bundle(building,geometry,front_width_studs)
    primary=building.volumes[0]
    studs_per_meter=front_width_studs/primary.width
    plates_per_meter=studs_per_meter*COURSES_PER_STUD_RATIO*3
    min_x=min(v.position.x for v in building.volumes); min_y=min(v.position.y for v in building.volumes); min_z=min(v.position.z for v in building.volumes)
    roofs_by_volume={r.volume_id:r for r in building.roofs}
    all_parts=[]; max_x=max_y=max_z=1
    for volume in building.volumes:
        subgeometry=_volume_geometry(geometry,volume.id)
        shell=generate_building_brick_shell(subgeometry,studs_per_meter=studs_per_meter)
        spatial_shell=generate_spatial_brick_shell(shell)
        window_parts,fitted_window_ids=generate_window_assemblies(building,shell)
        facade_details=generate_window_surrounds(building,shell,skip_opening_ids=fitted_window_ids)
        roof=roofs_by_volume.get(volume.id)
        spatial_roof=generate_spatial_gable_roof(subgeometry,shell) if roof is not None and roof.type is RoofType.GABLE else None
        local_model=generate_brick_model(spatial_shell,spatial_roof,facade_details,window_parts)
        x=round((volume.position.x-min_x)*studs_per_meter); y=round((volume.position.y-min_y)*studs_per_meter); z=round((volume.position.z-min_z)*plates_per_meter)
        all_parts.extend(_translate_model(local_model,prefix=volume.id,x=x,y=y,z=z))
        max_x=max(max_x,x+local_model.width_studs); max_y=max(max_y,y+local_model.depth_studs); max_z=max(max_z,z+local_model.height_plates)
    brick_model=BrickModel(building_id=building.id,volume_id="composite",width_studs=max_x,depth_studs=max_y,height_plates=max_z,parts=all_parts)
    bom=generate_bom(brick_model); assembly_plan=generate_assembly_plan(brick_model)
    return create_export_bundle(brick_model,bom,assembly_plan,appearance=building.appearance)

def run_m0_pipeline_scene(scene:ArchitecturalScene,*,front_width_studs:int=DEFAULT_FRONT_WIDTH_STUDS)->BrickExportBundle:
    """Build a validated Scene while preserving platforms and stairs in the LEGO model."""
    projection=project_scene_to_building(scene)
    if projection.building is None or projection.blocked:
        blockers=" ".join(issue.message for issue in projection.issues if issue.severity.value=="blocker")
        raise ValueError(blockers or "ArchitecturalScene cannot be projected to BuildingModel")
    base=run_m0_pipeline_model(projection.building,front_width_studs=front_width_studs)
    enriched=augment_brick_model_with_scene_architecture(base.brick_model,scene,front_width_studs=front_width_studs)
    if enriched is base.brick_model:
        return base
    bom=generate_bom(enriched)
    assembly_plan=generate_assembly_plan(enriched)
    return create_export_bundle(enriched,bom,assembly_plan,appearance=projection.building.appearance)

def run_m0_pipeline(input_path:str|Path,*,front_width_studs:int=DEFAULT_FRONT_WIDTH_STUDS)->BrickExportBundle:
    building=load_building_model(input_path); return run_m0_pipeline_model(building,front_width_studs=front_width_studs)
def write_m0_export(input_path:str|Path,output_path:str|Path,*,front_width_studs:int=DEFAULT_FRONT_WIDTH_STUDS)->BrickExportBundle:
    bundle=run_m0_pipeline(input_path,front_width_studs=front_width_studs); destination=Path(output_path); destination.parent.mkdir(parents=True,exist_ok=True); destination.write_text(export_bundle_json(bundle)+"\n",encoding="utf-8"); return bundle
def build_parser()->argparse.ArgumentParser:
    parser=argparse.ArgumentParser(prog="brickhouse-m0",description="Generate a BrickHouse M0 BrickModel/BOM/AssemblyPlan JSON export from a BuildingModel JSON file.")
    parser.add_argument("input",type=Path,help="BuildingModel JSON input"); parser.add_argument("output",type=Path,help="Output export JSON path")
    parser.add_argument("--front-width-studs",type=int,default=DEFAULT_FRONT_WIDTH_STUDS,help=f"target front facade width in studs (default: {DEFAULT_FRONT_WIDTH_STUDS})")
    return parser
def main(argv:list[str]|None=None)->int:
    args=build_parser().parse_args(argv); bundle=write_m0_export(args.input,args.output,front_width_studs=args.front_width_studs)
    print(f"Generated {args.output}: {bundle.bom.total_parts} parts, {bundle.bom.unique_part_types} canonical types, {bundle.assembly_plan.total_steps if bundle.assembly_plan else 0} assembly steps")
    return 0
if __name__=="__main__": raise SystemExit(main())
