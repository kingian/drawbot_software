#!/usr/bin/env ruby
require 'rubygems'
require 'bundler/setup'
require 'savage'
require 'nokogiri'
require 'optparse'

include Savage::Directions

class PenUp; end
class PenDown; end

class Savage::Directions::Point
  def inspect
    "(x:#{x}, y:#{y})"
  end

  def *(a)
    self.class.new(x * a, y * a)
  end

  def +(p)
    self.class.new(x + p.x, y + p.y)
  end

  def -(p)
    self.class.new(x - p.x, y - p.y)
  end

  def round(*args)
    self.class.new(x.round(*args), y.round(*args))
  end

  def distance_to(p)
    Math.sqrt((x - p.x) ** 2 + (y - p.y) ** 2)
  end
end

def interpolate_spline(p0, p1, p2, p3, t)
  p0 * (1.0 - t)**3 + p1 * 3 * (1.0 - t)**2 * t + p2 * 3 * (1.0 - t) * t**2 + p3 * t**3
end

def segment_spline(p0, p1, p2, p3, max_distance=1.0)
  t_count = 1
  raise 'p0' unless p0
  raise 'p1' unless p1
  raise 'p2' unless p2
  raise 'p3' unless p3
  while (dist = p0.distance_to(interpolate_spline(p0, p1, p2, p3, 1.0 / (t_count + 1)))) > max_distance
    t_count *= 2
  end
  ts = (1..t_count).map{|t| t.to_f / (t_count + 1)}
  [p0] + ts.map{|t| interpolate_spline(p0, p1, p2, p3, t)} + [p3]
end

class Savage::Path
  def to_line_segments(step_size=1.0)
    start_position = nil
    current_position = Point.new(0, 0)
    reflection = nil
    subpaths.map do |subpath|
      subpath.directions.map do |direction|
        reflection = nil unless direction.is_a?(CubicCurveTo) or direction.is_a?(QuadraticCurveTo)
        case direction
        when MoveTo
          if direction.absolute?
            current_position = direction.target
            start_position = current_position
          else
            current_position += direction.target
            start_position = current_position
          end
          [PenUp, current_position]
        when LineTo
          if direction.absolute?
            current_position = direction.target
          else
            current_position += direction.target
          end
          [PenDown, current_position]
        when VerticalTo
          if direction.absolute?
            current_position.y = direction.target
          else
            current_position.y += direction.target
          end
          [PenDown, current_position]
        when HorizontalTo
          if direction.absolute?
            current_position.x = direction.target
          else
            current_position.x += direction.target
          end
          [PenDown, current_position]
        when CubicCurveTo
          old_position = current_position.clone
          if direction.absolute?
            current_position = direction.target
            c1 = direction.control_1 || reflection
            c2 = direction.control_2
          else
            current_position += direction.target
            c1 = (direction.control_1 && (direction.control_1 + old_position)) || reflection
            c2 = direction.control_2 + old_position
          end
          reflection = (c2 - current_position) * -1 + current_position
          [PenDown] + segment_spline(old_position, c1, c2, current_position, step_size)
        when QuadraticCurveTo
          old_position = current_position.clone
          if direction.absolute?
            current_position = direction.target
            c = direction.control || reflection
          else
            current_position += direction.target
            c = (direction.control && (direction.control + old_position)) || reflection
          end
          c1 = old_position + (c - old_position) * (2.0 / 3.0)
          c2 = current_position + (c - current_position) * (2.0 / 3.0)
          reflection = (c - current_position) * -1 + current_position
          [PenDown] + segment_spline(old_position, c1, c2, current_position, step_size)
        when ClosePath
          [PenDown, start_position]
        else
          direction.inspect
          raise direction.inspect
        end
      end
    end.flatten
  end
end

def gcodify(svg_text, opts={})
  doc = Nokogiri.XML(svg_text)
  path_els = doc.search('path')
  paths = path_els.map {|el| Savage::Parser.parse el['d']}
  svg_el = doc.search('svg').first
  if viewbox = svg_el['viewBox']
    x0, y0, x1, y1 = viewbox.split.map(&:to_f)
    width = (x1 - x0).abs.to_f
    height = (y1 - y0).abs.to_f
  else
    width = svg_el['width'].to_f
    height = svg_el['height'].to_f
  end
  max_dim = [width, height].max
  scale = OPTS[:size].to_f / max_dim

  pendown = false
  segments = paths.map{|p| p.to_line_segments(OPTS[:segment_length] / scale)}.flatten

  preamble = ['G21 G90 G94 G92 X0 Y0 Z0']
  epilogue = ['G0 Z0 M30']
  gcodes = segments.map do |segment|
    if segment.is_a? Point
      "G1 X#{(scale * (segment.x - 0.5 * width)).round(2)} Y#{(scale * (segment.y - 0.5 * height) * (OPTS[:flip] ? -1 : 1)).round(2)}"
    elsif segment == PenDown
      unless pendown
        pendown = true
        "G1 Z15"
      end
    elsif segment == PenUp
      if pendown
        pendown = false
        "G1 Z0"
      end
    else
      raise segment.inspect
    end
  end.compact
  preamble + gcodes + epilogue
end

OPTS = {size: 100.0, flip: true, segment_length: 1.5, output_directory: '.'}
op = OptionParser.new do |x|
  x.banner = 'rsvg-gcodifier <options> <files>'
  x.separator ''

  x.on("-s", "--size NUM", Float, "Desired maximum dimension in mm (default: 100.0)") {|s| OPTS[:size] = s }

  x.on("-f", "--[no-]flip", "Flip on the Y axis (default: yes)") {|f| OPTS[:flip] = f }

  x.on("-l", "--segment-length NUM", Float, "Maximum spline line segment length in mm (default: 1.5)") { |l| OPTS[:segment_length] = l }

  x.on("-o", "--output-directory DIR", String, "GCode output directory (default: .)") { |o| OPTS[:output_directory] = o }

  x.on("-h", "--help", "Show this message") { puts op;  exit }
end

op.parse!(ARGV)

ARGV.each do |infile|
  outfile = File.join(OPTS[:output_directory], "#{File.basename(infile, '.*')}.gcode")
  puts "#{infile} -> #{outfile}"
  File.write(outfile, gcodify(File.read(infile), OPTS).join("\n"))
end
