"""Rebuild the bundled fictional datasheet. Requires reportlab (optional dev dependency)."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT=Path(__file__).resolve().parent
out=ROOT/'sample'/'SC100_Fictional_Datasheet.pdf'
out.parent.mkdir(exist_ok=True)
font_dir=Path('/usr/share/fonts/truetype/dejavu')
if (font_dir/'DejaVuSans.ttf').exists():
 pdfmetrics.registerFont(TTFont('Helvetica',str(font_dir/'DejaVuSans.ttf')))
 pdfmetrics.registerFont(TTFont('Helvetica-Bold',str(font_dir/'DejaVuSans-Bold.ttf')))
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Eyebrow',fontName='Helvetica-Bold',fontSize=9,textColor=colors.HexColor('#287760'),spaceAfter=16))
styles['Title'].fontName='Helvetica-Bold'
styles['Title'].fontSize=30
styles['Title'].leading=35
styles['Title'].alignment=TA_LEFT
styles['BodyText'].leading=15
styles['BodyText'].spaceAfter=10

def table(rows,widths):
 t=Table(rows,colWidths=widths,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf1ed')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#ccd7d0')),('VALIGN',(0,0),(-1,-1),'TOP')]))
 return t

story=[Paragraph('SPECCHECK / FICTIONAL REFERENCE',styles['Eyebrow']),Paragraph('SC100<br/>Sensor Controller',styles['Title']),Paragraph('Demonstration datasheet - Revision A',styles['BodyText']),Spacer(1,18),Paragraph('1. Temperature specifications',styles['Heading2']),Paragraph('These are separate specifications. A storage rating does not establish an allowable operating condition.',styles['BodyText']),table([['Specification','Value'],['Operating ambient temperature','-40 to +85 °C'],['Storage temperature','-55 to +125 °C']],[300,190]),Spacer(1,20),Paragraph('Operating ambient temperature: -40 to +85 °C.',styles['BodyText']),Paragraph('Storage temperature: -55 to +125 °C.',styles['BodyText']),Spacer(1,12),Paragraph('Scope',styles['Heading2']),Paragraph('This document describes the fictional SC100 component only. All values are invented for software demonstrations. Do not use them for component selection or engineering decisions.',styles['BodyText']),PageBreak(),Paragraph('SPECCHECK / FICTIONAL REFERENCE',styles['Eyebrow']),Paragraph('Electrical characteristics',styles['Title']),Paragraph('2. Supply current',styles['Heading2']),table([['Parameter','Typical value','Test conditions'],['Supply current','30 mA','25 °C, VDD = 3.3 V']],[180,120,190]),Spacer(1,20),Paragraph('Typical supply current: 30 mA at 25 °C and VDD = 3.3 V.',styles['BodyText']),Paragraph('The current is a typical value under the stated test conditions. It is not a guaranteed maximum across all temperatures and supply voltages.',styles['BodyText']),Spacer(1,18),Paragraph('3. Reliability information',styles['Heading2']),Paragraph('This excerpt covers temperature and supply current. Reliability test results are outside its scope.',styles['BodyText']),Spacer(1,18),Paragraph('Reading notes',styles['Heading2']),Paragraph('Check the type of limit, units, and test conditions before applying a value. Preserve table headings and nearby explanatory text when extracting this document.',styles['BodyText'])]

def footer(c,d):
 c.setStrokeColor(colors.HexColor('#ccd7d0'));c.line(52,48,543,48)
 c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#64756b'))
 c.drawString(52,34,'SC100 / FICTIONAL SAMPLE / REV A');c.drawRightString(543,34,f'{d.page} / 2')

SimpleDocTemplate(str(out),pagesize=(595,842),leftMargin=52,rightMargin=52,topMargin=48,bottomMargin=65).build(story,onFirstPage=footer,onLaterPages=footer)
print(out)
